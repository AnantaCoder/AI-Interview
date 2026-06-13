"""
WebSocket-based real-time proctoring router.

Flow:
1. Client connects: ws://host/api/v1/ws/proctoring/{interview_id}?token=<JWT>
2. Client sends base64-encoded JPEG frames every 200-500ms
3. Server processes each frame through the CV pipeline
4. Server sends back real-time metrics JSON
5. On disconnect: final scores are computed and saved to DB
"""
import base64
import json
import time
import logging

import numpy as np
import cv2
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.db.session import get_session_maker
from app.db.models.interview import Interview, InterviewStatus, ProctorSession
from app.utils.security import verify_access_token
from app.cv.frame_analyzer import analyze_frame
from app.cv.score_aggregator import ScoreAggregator
from app.cv.metrics import FrameMetrics, SessionMetrics, RealTimeUpdate

logger = logging.getLogger("routers.proctoring")

router = APIRouter(tags=["Proctoring"])


async def _authenticate_ws(websocket: WebSocket) -> str | None:
    """
    Authenticate WebSocket connection via token query parameter.
    Returns user_id or None.
    """
    token = websocket.query_params.get("token")
    if not token:
        return None
    
    payload = verify_access_token(token)
    if payload is None:
        return None
    
    return payload.get("sub")


async def _get_or_create_proctor_session(interview_id: str) -> str | None:
    """
    Get or create a ProctorSession for the given interview.
    Returns the proctor session ID, or None if interview not found.
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Verify interview exists and is in progress
        result = await session.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        if not interview:
            return None
        
        # Check for existing proctor session
        result = await session.execute(
            select(ProctorSession).where(ProctorSession.interview_id == interview_id)
        )
        proctor = result.scalar_one_or_none()
        
        if not proctor:
            proctor = ProctorSession(interview_id=interview_id)
            session.add(proctor)
            await session.commit()
            await session.refresh(proctor)
        
        return str(proctor.id)


async def _save_final_scores(
    interview_id: str,
    aggregator: ScoreAggregator,
    event_log: list[dict],
) -> None:
    """Save final aggregated scores to DB when session ends."""
    scores = aggregator.compute_scores()
    signals = aggregator.get_signal_counts()
    emotions = aggregator.get_emotion_distribution()
    
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Update ProctorSession
        result = await session.execute(
            select(ProctorSession).where(ProctorSession.interview_id == interview_id)
        )
        proctor = result.scalar_one_or_none()
        
        if proctor:
            proctor.total_frames = signals["total_frames"]
            proctor.confidence_score = scores.confidence
            proctor.attention_score = scores.attention
            proctor.integrity_score = scores.integrity
            proctor.posture_score = scores.posture
            proctor.face_not_visible_count = signals["face_not_visible_count"]
            proctor.gaze_away_count = signals["gaze_away_count"]
            proctor.head_turn_count = signals["head_turn_count"]
            proctor.multi_person_count = signals["multi_person_count"]
            proctor.excessive_movement_count = signals["excessive_movement_count"]
            proctor.emotion_distribution = emotions
            proctor.event_log = event_log[-100:]  # Keep last 100 events
        
        # Update Interview with video scores
        result = await session.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        
        if interview:
            interview.video_confidence_score = scores.confidence
            interview.video_attention_score = scores.attention
            interview.video_integrity_score = scores.integrity
        
        await session.commit()
    
    logger.info(
        f"Saved proctor scores for interview {interview_id}: "
        f"confidence={scores.confidence}, attention={scores.attention}, "
        f"integrity={scores.integrity}, posture={scores.posture}, "
        f"frames={signals['total_frames']}"
    )


@router.websocket("/ws/proctoring/{interview_id}")
async def proctoring_ws(websocket: WebSocket, interview_id: str):
    """
    Real-time proctoring WebSocket endpoint.
    
    Client sends: base64-encoded JPEG frame as text message
    Server responds: JSON with real-time metrics after each frame
    """
    # 1. Authenticate
    user_id = await _authenticate_ws(websocket)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or missing token")
        return
    
    # 2. Validate interview
    proctor_id = await _get_or_create_proctor_session(interview_id)
    if not proctor_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Interview not found")
        return
    
    # 3. Accept connection
    await websocket.accept()
    logger.info(f"Proctoring WebSocket connected for interview {interview_id}")
    
    # 4. Initialize CV pipeline
    aggregator = ScoreAggregator()
    event_log = []
    frame_number = 0
    
    try:
        while True:
            # Receive base64 frame from client
            data = await websocket.receive_text()
            
            try:
                # Decode base64 → bytes → numpy array
                # Strip data URL prefix if present (e.g., "data:image/jpeg;base64,...")
                if "," in data:
                    data = data.split(",", 1)[1]
                
                img_bytes = base64.b64decode(data)
                nparr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    await websocket.send_json({"error": "Failed to decode frame"})
                    continue
                
                frame_number += 1
                
                # Analyze frame
                raw_metrics = analyze_frame(frame)
                metrics = FrameMetrics(**raw_metrics)
                
                # Feed into aggregator
                aggregator.add_frame(metrics)
                
                # Generate alerts
                alerts = []
                timestamp = time.time()
                
                if not metrics.face_visible:
                    alerts.append("Face not detected")
                    event_log.append({"time": timestamp, "event": "face_not_visible", "frame": frame_number})
                
                if not metrics.gaze_on_screen:
                    alerts.append("Looking away from screen")
                
                if metrics.head_turned_away:
                    alerts.append("Head turned away")
                    event_log.append({"time": timestamp, "event": "head_turned", "frame": frame_number, "yaw": metrics.head_yaw})
                
                if metrics.multi_person_detected:
                    alerts.append(f"Multiple people detected ({metrics.person_count})")
                    event_log.append({"time": timestamp, "event": "multi_person", "frame": frame_number, "count": metrics.person_count})
                
                if metrics.excessive_movement:
                    alerts.append("Excessive body movement")
                
                # Compute running scores
                current_scores = aggregator.compute_scores()
                
                # Build response
                update = RealTimeUpdate(
                    frame_number=frame_number,
                    face_visible=metrics.face_visible,
                    gaze_on_screen=metrics.gaze_on_screen,
                    head_turned_away=metrics.head_turned_away,
                    dominant_emotion=metrics.dominant_emotion,
                    person_count=metrics.person_count,
                    multi_person_detected=metrics.multi_person_detected,
                    posture_quality=metrics.posture_quality,
                    excessive_movement=metrics.excessive_movement,
                    current_scores=current_scores,
                    alerts=alerts,
                )
                
                await websocket.send_json(update.model_dump())
                
            except Exception as e:
                logger.error(f"Frame processing error: {e}")
                await websocket.send_json({"error": f"Processing error: {str(e)}"})
    
    except WebSocketDisconnect:
        logger.info(f"Proctoring WebSocket disconnected for interview {interview_id} after {frame_number} frames")
    except Exception as e:
        logger.error(f"WebSocket error for interview {interview_id}: {e}")
    finally:
        # Save final scores to database
        if frame_number > 0:
            await _save_final_scores(interview_id, aggregator, event_log)
