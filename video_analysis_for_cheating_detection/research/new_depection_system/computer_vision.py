import cv2
import mediapipe as mp
import numpy as np

class CheatingDetection:
    def __init__(self):
        # Initialize MediaPipe Face Mesh with iris tracking enabled
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=5,
            refine_landmarks=True,  # Crucial for iris tracking
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.lip_distances = []
        
    def detect_cheating(self, frame):
        """
        Processes a frame, evaluates multiple cheating metrics,
        and returns a violation state dictionary.
        """
        # Convert BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        violations = {
            'multiple_faces': False,
            'head_pose_violation': False,
            'eye_gaze_violation': False,
            'mouth_movement': False,
            'tab_switch': False
        }
        
        if not results.multi_face_landmarks:
            return violations, frame
            
        # 1. Check Multiple Faces
        if len(results.multi_face_landmarks) > 1:
            violations['multiple_faces'] = True
            
        # Analyze the primary (closest/first) face
        face_landmarks = results.multi_face_landmarks[0]
        h, w, _ = frame.shape
        
        # 2. Check Head Pose Violation
        violations['head_pose_violation'] = self.check_head_pose(face_landmarks, w, h)
        
        # 3. Check Eye Gaze Violation
        violations['eye_gaze_violation'] = self.check_eye_gaze(face_landmarks, w, h)
        
        # 4. Check Lip/Mouth movement
        violations['mouth_movement'] = self.detect_speech(face_landmarks, w, h)
        
        # Visual cues for testing
        self.draw_debug_overlays(frame, face_landmarks, violations, w, h)
        
        return violations, frame

    def check_head_pose(self, face_landmarks, w, h):
        """
        Uses standard facial landmarks to estimate head orientation (pitch/yaw/roll).
        """
        # Selected 3D facial landmarks (Nose, Chin, Eyes, Mouth)
        image_points = np.array([
            (face_landmarks.landmark[1].x * w, face_landmarks.landmark[1].y * h),       # Nose tip
            (face_landmarks.landmark[152].x * w, face_landmarks.landmark[152].y * h),   # Chin
            (face_landmarks.landmark[33].x * w, face_landmarks.landmark[33].y * h),     # Left eye corner
            (face_landmarks.landmark[263].x * w, face_landmarks.landmark[263].y * h),   # Right eye corner
            (face_landmarks.landmark[61].x * w, face_landmarks.landmark[61].y * h),     # Left mouth corner
            (face_landmarks.landmark[291].x * w, face_landmarks.landmark[291].y * h)    # Right mouth corner
        ], dtype="double")
        
        model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye left corner
            (225.0, 170.0, -135.0),      # Right eye right corner
            (-150.0, -150.0, -125.0),    # Left mouth corner
            (150.0, -150.0, -125.0)      # Right mouth corner
        ])
        
        # Camera internal parameters
        focal_length = w
        center = (w/2, h/2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype="double")
        
        dist_coeffs = np.zeros((4,1))
        (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)
        
        rmat, _ = cv2.Rodrigues(rotation_vector)
        angles, _, _, _, _, _ = cv2.RQDecomposeMatrix(rmat)
        
        pitch = angles[0]
        yaw = angles[1]
        
        # Flags suspicious head turns (> 25 deg left/right, > 15 deg up/down)
        if abs(yaw) > 25 or abs(pitch) > 15:
            return True
        return False

    def check_eye_gaze(self, face_landmarks, w, h):
        """
        Calculates horizontal gaze shift by iris vs. eye corner ratios.
        """
        left_iris = face_landmarks.landmark[468]
        left_eye_left = face_landmarks.landmark[33]
        left_eye_right = face_landmarks.landmark[133]
        
        # Simple ratio evaluation
        iris_x = left_iris.x
        left_x = left_eye_left.x
        right_x = left_eye_right.x
        
        if (right_x - left_x) == 0:
            return False
            
        ratio = (iris_x - left_x) / (right_x - left_x)
        
        # Extreme left or right gazing
        if ratio < 0.35 or ratio > 0.65:
            return True
        return False

    def detect_speech(self, face_landmarks, w, h):
        """
        Flags continuous lip variance indicative of talking.
        """
        lip_upper = face_landmarks.landmark[13]
        lip_lower = face_landmarks.landmark[14]
        
        distance = abs(lip_upper.y - lip_lower.y)
        self.lip_distances.append(distance)
        
        if len(self.lip_distances) > 10:
            self.lip_distances.pop(0)
            
        if len(self.lip_distances) >= 5:
            std_dev = np.std(self.lip_distances)
            if std_dev > 0.005: 
                return True
        return False

    def draw_debug_overlays(self, frame, landmarks, violations, w, h):
        # Nose point
        nose = (int(landmarks.landmark[1].x * w), int(landmarks.landmark[1].y * h))
        cv2.circle(frame, nose, 4, (0, 255, 255), -1)
        
        # Warning overlays
        offset = 30
        for violation, value in violations.items():
            color = (0, 0, 255) if value else (0, 255, 0)
            text = f"{violation.replace('_', ' ').capitalize()}: {'⚠️ YES' if value else 'OK'}"
            cv2.putText(frame, text, (20, offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            offset += 25
