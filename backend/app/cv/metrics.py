"""
Pydantic models for frame-level and session-level CV metrics.
"""
from pydantic import BaseModel, Field
from typing import Optional


class FrameMetrics(BaseModel):
    """Metrics extracted from a single video frame."""
    
    # Face Detection
    face_visible: bool = Field(default=False, description="Whether a face is detected")
    
    # Eye Gaze
    gaze_on_screen: bool = Field(default=True, description="Whether candidate is looking at screen")
    gaze_ratio: float = Field(default=0.5, ge=0.0, le=1.0, description="Horizontal gaze ratio (0=left, 0.5=center, 1=right)")
    
    # Head Pose
    head_yaw: float = Field(default=0.0, description="Head rotation left/right in degrees")
    head_pitch: float = Field(default=0.0, description="Head rotation up/down in degrees")
    head_roll: float = Field(default=0.0, description="Head tilt in degrees")
    head_turned_away: bool = Field(default=False, description="Whether head is significantly turned")
    
    # Emotion
    dominant_emotion: str = Field(default="neutral", description="Detected emotion")
    emotion_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence of emotion detection")
    
    # Posture
    posture_quality: float = Field(default=80.0, ge=0.0, le=100.0, description="Posture quality score")
    excessive_movement: bool = Field(default=False, description="Whether excessive body movement detected")
    
    # Multi-Person
    person_count: int = Field(default=1, ge=0, description="Number of people detected in frame")
    multi_person_detected: bool = Field(default=False, description="Whether more than one person is detected")


class SessionMetrics(BaseModel):
    """Aggregated metrics for the entire proctoring session."""
    confidence: float = Field(default=100.0, ge=0.0, le=100.0, description="Confidence score")
    attention: float = Field(default=100.0, ge=0.0, le=100.0, description="Attention score")
    integrity: float = Field(default=100.0, ge=0.0, le=100.0, description="Integrity score")
    posture: float = Field(default=100.0, ge=0.0, le=100.0, description="Posture score")


class RealTimeUpdate(BaseModel):
    """Message sent back to the client after each frame."""
    frame_number: int
    face_visible: bool
    gaze_on_screen: bool
    head_turned_away: bool
    dominant_emotion: str
    person_count: int
    multi_person_detected: bool
    posture_quality: float
    excessive_movement: bool
    # Running session scores
    current_scores: SessionMetrics
    # Alerts (warnings for the candidate or proctor)
    alerts: list[str] = Field(default_factory=list)
