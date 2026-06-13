"""
Core computer vision engine for interview proctoring.

Uses:
- MediaPipe Face Detection: Detect face presence
- MediaPipe Face Mesh (468 landmarks): Eye gaze + head pose + emotion
- MediaPipe Pose: Posture analysis
- YOLOv8n: Multi-person detection
"""
import numpy as np
import cv2
import math
import logging

logger = logging.getLogger("cv.frame_analyzer")

# Lazy-loaded globals for heavy models
_face_mesh = None
_pose = None
_yolo_model = None
_prev_landmarks = None


def _get_face_mesh():
    """Lazy-load MediaPipe Face Mesh."""
    global _face_mesh
    if _face_mesh is None:
        import mediapipe as mp
        _face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,  # Enables iris landmarks (468-477)
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        logger.info("MediaPipe Face Mesh initialized")
    return _face_mesh


def _get_pose():
    """Lazy-load MediaPipe Pose."""
    global _pose
    if _pose is None:
        import mediapipe as mp
        _pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=0,  # Lightweight
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        logger.info("MediaPipe Pose initialized")
    return _pose


def _get_yolo():
    """Lazy-load YOLOv8n model."""
    global _yolo_model
    if _yolo_model is None:
        from ultralytics import YOLO
        _yolo_model = YOLO("yolov8n.pt")
        logger.info("YOLOv8n model initialized")
    return _yolo_model


def _estimate_head_pose(landmarks, img_w: int, img_h: int) -> tuple[float, float, float]:
    """
    Estimate head pose (yaw, pitch, roll) using Face Mesh 3D landmarks
    and cv2.solvePnP.
    
    Returns (yaw, pitch, roll) in degrees.
    """
    # 6 key facial landmarks for PnP
    # Nose tip, Chin, Left eye corner, Right eye corner, Left mouth, Right mouth
    face_2d = []
    face_3d = []
    
    key_indices = [1, 152, 33, 263, 61, 291]
    
    for idx in key_indices:
        lm = landmarks[idx]
        x, y = int(lm.x * img_w), int(lm.y * img_h)
        face_2d.append([x, y])
        face_3d.append([lm.x * img_w, lm.y * img_h, lm.z * 3000])
    
    face_2d = np.array(face_2d, dtype=np.float64)
    face_3d = np.array(face_3d, dtype=np.float64)
    
    # Camera matrix approximation
    focal_length = img_w
    cam_matrix = np.array([
        [focal_length, 0, img_w / 2],
        [0, focal_length, img_h / 2],
        [0, 0, 1]
    ], dtype=np.float64)
    
    dist_coeffs = np.zeros((4, 1), dtype=np.float64)
    
    success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_coeffs)
    
    if not success:
        return 0.0, 0.0, 0.0
    
    rmat, _ = cv2.Rodrigues(rot_vec)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
    
    yaw = angles[1] * 360    # Left/Right
    pitch = angles[0] * 360  # Up/Down
    roll = angles[2] * 360   # Tilt
    
    return float(yaw), float(pitch), float(roll)


def _analyze_gaze(landmarks, img_w: int, img_h: int) -> tuple[bool, float]:
    """
    Analyze eye gaze using iris landmarks from Face Mesh.
    
    Returns (is_looking_at_screen, gaze_ratio).
    """
    # Left eye corners: 33 (outer), 133 (inner)
    # Left iris center: 468
    # Right eye corners: 362 (outer), 263 (inner)
    # Right iris center: 473
    
    try:
        # Left eye
        l_outer = landmarks[33]
        l_inner = landmarks[133]
        l_iris = landmarks[468]
        
        # Right eye
        r_outer = landmarks[362]
        r_inner = landmarks[263]
        r_iris = landmarks[473]
        
        # Calculate horizontal gaze ratio for each eye
        l_eye_width = abs(l_inner.x - l_outer.x)
        l_iris_pos = abs(l_iris.x - l_outer.x)
        l_ratio = l_iris_pos / l_eye_width if l_eye_width > 0 else 0.5
        
        r_eye_width = abs(r_inner.x - r_outer.x)
        r_iris_pos = abs(r_iris.x - r_outer.x)
        r_ratio = r_iris_pos / r_eye_width if r_eye_width > 0 else 0.5
        
        avg_ratio = (l_ratio + r_ratio) / 2.0
        avg_ratio = max(0.0, min(1.0, avg_ratio))
        
        # Looking at screen if gaze is roughly centered (0.25–0.75)
        is_looking = 0.20 <= avg_ratio <= 0.80
        
        return is_looking, avg_ratio
    except (IndexError, ZeroDivisionError):
        return True, 0.5


def _detect_emotion(landmarks) -> tuple[str, float]:
    """
    Simple emotion detection using facial landmark distances.
    
    Analyzes mouth opening, eyebrow position, and eye openness.
    Returns (emotion_name, confidence).
    """
    try:
        # Mouth opening: distance between upper lip (13) and lower lip (14)
        mouth_open = abs(landmarks[13].y - landmarks[14].y)
        
        # Mouth width: distance between corners (61, 291)
        mouth_width = abs(landmarks[61].x - landmarks[291].x)
        mouth_ratio = mouth_open / mouth_width if mouth_width > 0 else 0
        
        # Eyebrow raise: distance from eyebrow (70) to eye (159) - left side
        brow_raise = abs(landmarks[70].y - landmarks[159].y)
        
        # Eye openness: upper eyelid (159) to lower eyelid (145)
        eye_open = abs(landmarks[159].y - landmarks[145].y)
        
        # Simple classification based on ratios
        if mouth_ratio > 0.35:
            # Wide mouth = surprised or stressed
            return "surprised", 0.7
        elif mouth_ratio > 0.15 and mouth_width > 0.12:
            # Smile
            return "happy", 0.65
        elif brow_raise < 0.02 and eye_open < 0.015:
            # Furrowed brows, narrow eyes
            return "stressed", 0.6
        elif eye_open < 0.012:
            return "nervous", 0.55
        else:
            return "neutral", 0.8
    except (IndexError, ZeroDivisionError):
        return "neutral", 0.5


def _analyze_posture(pose_landmarks, img_h: int) -> tuple[float, bool]:
    """
    Analyze sitting posture using MediaPipe Pose landmarks.
    
    Checks shoulder alignment, spine straightness, and body lean.
    Returns (posture_quality 0-100, excessive_movement).
    """
    global _prev_landmarks
    
    try:
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        
        # Key landmarks
        l_shoulder = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
        r_shoulder = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        l_hip = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP]
        r_hip = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]
        nose = pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE]
        
        # 1. Shoulder alignment (difference in Y between shoulders)
        shoulder_diff = abs(l_shoulder.y - r_shoulder.y)
        shoulder_score = max(0, 100 - shoulder_diff * 500)
        
        # 2. Spine straightness (nose should be between and above shoulders)
        mid_shoulder_x = (l_shoulder.x + r_shoulder.x) / 2
        lean = abs(nose.x - mid_shoulder_x)
        spine_score = max(0, 100 - lean * 400)
        
        # 3. Forward lean (nose Y relative to shoulder Y)
        forward_lean = max(0, nose.y - ((l_shoulder.y + r_shoulder.y) / 2))
        forward_score = max(0, 100 - forward_lean * 300)
        
        posture_quality = (shoulder_score * 0.3 + spine_score * 0.4 + forward_score * 0.3)
        posture_quality = max(0.0, min(100.0, posture_quality))
        
        # Check for excessive movement (compare with previous frame)
        excessive = False
        current_pos = np.array([nose.x, nose.y, l_shoulder.x, l_shoulder.y])
        
        if _prev_landmarks is not None:
            movement = np.linalg.norm(current_pos - _prev_landmarks)
            excessive = movement > 0.08  # Threshold for significant movement
        
        _prev_landmarks = current_pos
        
        return float(posture_quality), excessive
    except Exception:
        return 80.0, False


def _detect_multi_person(frame: np.ndarray) -> tuple[int, bool]:
    """
    Detect number of people in frame using YOLOv8n.
    
    Returns (person_count, is_multi_person).
    """
    try:
        model = _get_yolo()
        results = model(frame, classes=[0], conf=0.4, verbose=False)  # class 0 = person
        
        person_count = 0
        for r in results:
            person_count = len(r.boxes)
        
        return person_count, person_count > 1
    except Exception as e:
        logger.warning(f"YOLOv8 detection error: {e}")
        return 1, False


def analyze_frame(frame: np.ndarray) -> dict:
    """
    Main entry point: analyze a single video frame.
    
    Args:
        frame: BGR numpy array from OpenCV
        
    Returns:
        Dictionary of FrameMetrics fields
    """
    from app.cv.metrics import FrameMetrics
    
    img_h, img_w = frame.shape[:2]
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Defaults
    result = {
        "face_visible": False,
        "gaze_on_screen": True,
        "gaze_ratio": 0.5,
        "head_yaw": 0.0,
        "head_pitch": 0.0,
        "head_roll": 0.0,
        "head_turned_away": False,
        "dominant_emotion": "neutral",
        "emotion_confidence": 0.5,
        "posture_quality": 80.0,
        "excessive_movement": False,
        "person_count": 1,
        "multi_person_detected": False,
    }
    
    # --- Face Mesh (face detection + gaze + head pose + emotion) ---
    face_mesh = _get_face_mesh()
    face_results = face_mesh.process(rgb_frame)
    
    if face_results.multi_face_landmarks:
        landmarks = face_results.multi_face_landmarks[0].landmark
        result["face_visible"] = True
        
        # Eye Gaze
        gaze_on, gaze_ratio = _analyze_gaze(landmarks, img_w, img_h)
        result["gaze_on_screen"] = gaze_on
        result["gaze_ratio"] = gaze_ratio
        
        # Head Pose
        yaw, pitch, roll = _estimate_head_pose(landmarks, img_w, img_h)
        result["head_yaw"] = yaw
        result["head_pitch"] = pitch
        result["head_roll"] = roll
        result["head_turned_away"] = abs(yaw) > 30 or abs(pitch) > 25
        
        # Emotion
        emotion, confidence = _detect_emotion(landmarks)
        result["dominant_emotion"] = emotion
        result["emotion_confidence"] = confidence
    
    # --- Pose (posture analysis) ---
    pose = _get_pose()
    pose_results = pose.process(rgb_frame)
    
    if pose_results.pose_landmarks:
        posture_q, excess_move = _analyze_posture(pose_results.pose_landmarks, img_h)
        result["posture_quality"] = posture_q
        result["excessive_movement"] = excess_move
    
    # --- YOLOv8 (multi-person detection) ---
    person_count, multi = _detect_multi_person(frame)
    result["person_count"] = person_count
    result["multi_person_detected"] = multi
    
    return result
