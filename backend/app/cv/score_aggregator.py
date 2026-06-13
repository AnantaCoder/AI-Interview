"""
Score aggregator: converts per-frame signals into session-level scores.

Maintains a sliding window of frame metrics and computes running
scores for confidence, attention, integrity, and posture.
"""
from collections import Counter
from app.cv.metrics import FrameMetrics, SessionMetrics


class ScoreAggregator:
    """Aggregates per-frame CV metrics into session-level scores."""
    
    def __init__(self):
        self.frame_count = 0
        
        # Counters for each signal
        self.face_visible_count = 0
        self.gaze_on_screen_count = 0
        self.head_straight_count = 0
        self.multi_person_count = 0
        self.excessive_movement_count = 0
        
        # Posture quality accumulator
        self.posture_sum = 0.0
        
        # Emotion tracking
        self.emotion_counts = Counter()
        
        # Stability tracking (for confidence score)
        self._prev_gaze_ratio = None
        self._gaze_stability_sum = 0.0
        self._prev_emotion = None
        self._emotion_stability_count = 0
    
    def add_frame(self, metrics: FrameMetrics) -> None:
        """Record metrics from a single frame."""
        self.frame_count += 1
        
        # Face visibility
        if metrics.face_visible:
            self.face_visible_count += 1
        
        # Gaze
        if metrics.gaze_on_screen:
            self.gaze_on_screen_count += 1
        
        # Head pose
        if not metrics.head_turned_away:
            self.head_straight_count += 1
        
        # Multi-person
        if metrics.multi_person_detected:
            self.multi_person_count += 1
        
        # Movement
        if metrics.excessive_movement:
            self.excessive_movement_count += 1
        
        # Posture
        self.posture_sum += metrics.posture_quality
        
        # Emotion
        self.emotion_counts[metrics.dominant_emotion] += 1
        
        # Gaze stability (how much gaze moves between frames)
        if self._prev_gaze_ratio is not None:
            delta = abs(metrics.gaze_ratio - self._prev_gaze_ratio)
            self._gaze_stability_sum += (1.0 - min(delta * 5, 1.0))  # Penalize large shifts
        self._prev_gaze_ratio = metrics.gaze_ratio
        
        # Emotion stability (consistency of emotion across frames)
        if self._prev_emotion == metrics.dominant_emotion:
            self._emotion_stability_count += 1
        self._prev_emotion = metrics.dominant_emotion
    
    def compute_scores(self) -> SessionMetrics:
        """Compute aggregated session scores."""
        if self.frame_count == 0:
            return SessionMetrics()
        
        n = self.frame_count
        
        # === ATTENTION SCORE ===
        # Weighted combination of face visibility, gaze on screen, and head straight
        face_pct = (self.face_visible_count / n) * 100
        gaze_pct = (self.gaze_on_screen_count / n) * 100
        head_pct = (self.head_straight_count / n) * 100
        
        attention = face_pct * 0.3 + gaze_pct * 0.4 + head_pct * 0.3
        attention = max(0.0, min(100.0, attention))
        
        # === INTEGRITY SCORE ===
        # Starts at 100, penalized for multi-person events and face absence
        multi_penalty = min(50, self.multi_person_count * 10)  # -10 per multi-person frame, max -50
        face_absence_penalty = min(30, max(0, (n - self.face_visible_count) - 5) * 2)  # Allow 5 missing frames
        
        integrity = 100.0 - multi_penalty - face_absence_penalty
        integrity = max(0.0, min(100.0, integrity))
        
        # === CONFIDENCE SCORE ===
        # Based on gaze stability, emotion stability, and posture
        gaze_stability = (self._gaze_stability_sum / max(1, n - 1)) * 100 if n > 1 else 100
        emotion_stability = (self._emotion_stability_count / max(1, n - 1)) * 100 if n > 1 else 100
        avg_posture = self.posture_sum / n
        
        confidence = gaze_stability * 0.35 + emotion_stability * 0.30 + avg_posture * 0.35
        confidence = max(0.0, min(100.0, confidence))
        
        # === POSTURE SCORE ===
        movement_penalty = min(30, self.excessive_movement_count * 3)
        posture = avg_posture - movement_penalty
        posture = max(0.0, min(100.0, posture))
        
        return SessionMetrics(
            confidence=round(confidence, 1),
            attention=round(attention, 1),
            integrity=round(integrity, 1),
            posture=round(posture, 1),
        )
    
    def get_emotion_distribution(self) -> dict[str, int]:
        """Return emotion frequency distribution."""
        return dict(self.emotion_counts)
    
    def get_signal_counts(self) -> dict:
        """Return raw signal counters for database storage."""
        return {
            "total_frames": self.frame_count,
            "face_not_visible_count": self.frame_count - self.face_visible_count,
            "gaze_away_count": self.frame_count - self.gaze_on_screen_count,
            "head_turn_count": self.frame_count - self.head_straight_count,
            "multi_person_count": self.multi_person_count,
            "excessive_movement_count": self.excessive_movement_count,
        }
