import cv2
import dlib
import numpy as np
from scipy.spatial import distance

# Initialize face detector and landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Eye landmark indices
LEFT_EYE = list(range(36, 42))
RIGHT_EYE = list(range(42, 48))

# Constants
EAR_THRESHOLD = 0.25  # Eye aspect ratio threshold for blink detection
GAZE_STD_THRESHOLD = 5.0  # Threshold for gaze direction standard deviation
CONSECUTIVE_FRAMES = 15  # Number of frames for cheating detection

# Define regions of interest (ROIs)
QUESTION_REGION = (100, 100, 300, 200)  # (x1, y1, x2, y2) for question area
ANSWER_REGION = (400, 100, 600, 200)    # (x1, y1, x2, y2) for answer area
MIN_TIME_IN_REGION = 10  # Minimum frames to consider as "spending time" in a region

def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def get_gaze_ratio(eye_points, landmarks):
    eye_region = np.array([(landmarks.part(point).x, landmarks.part(point).y)
                           for point in eye_points], dtype=np.int32)
    eye_center = np.mean(eye_region, axis=0).astype(int)
    return eye_center

def is_gaze_in_region(gaze_center, region):
    x, y = gaze_center
    x1, y1, x2, y2 = region
    return x1 <= x <= x2 and y1 <= y <= y2

# Initialize variables
cheat_counter = 0
gaze_history = []
current_region = None
time_in_region = 0
region_transitions = []  # Tracks transitions between regions
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if frame is None or frame.size == 0:
        continue

    # Ensure grayscale, 8-bit unsigned integer, and contiguous in memory for dlib C++ backend
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = np.ascontiguousarray(gray, dtype=np.uint8)
    
    faces = detector(gray)
    cheating_detected = False

    for face in faces:
        landmarks = predictor(gray, face)

        # Get eye landmarks
        left_eye = np.array([(landmarks.part(n).x, landmarks.part(n).y) for n in LEFT_EYE])
        right_eye = np.array([(landmarks.part(n).x, landmarks.part(n).y) for n in RIGHT_EYE])

        # Calculate eye centers
        left_center = get_gaze_ratio(LEFT_EYE, landmarks)
        right_center = get_gaze_ratio(RIGHT_EYE, landmarks)
        avg_center = ((left_center[0] + right_center[0]) // 2,
                      (left_center[1] + right_center[1]) // 2)

        # Store gaze history
        gaze_history.append(avg_center)
        if len(gaze_history) > 30:  # Keep last 1 second of data (assuming 30fps)
            gaze_history.pop(0)

        # Calculate gaze variation
        if len(gaze_history) > 10:
            gaze_std = np.std(gaze_history, axis=0)
            total_std = gaze_std[0] + gaze_std[1]

            # Detect irregular gaze patterns
            if total_std < GAZE_STD_THRESHOLD:
                # Check if gaze is fixed but not centered
                frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)
                distance_from_center = distance.euclidean(avg_center, frame_center)

                if distance_from_center > 100:  # If staring at edge of screen
                    cheat_counter += 2
                else:
                    cheat_counter = max(0, cheat_counter - 1)
            else:
                # Check for rapid eye movements
                movement_changes = sum(
                    1 for i in range(1, len(gaze_history))
                    if distance.euclidean(gaze_history[i], gaze_history[i - 1]) > 5
                )

                if movement_changes > 15:  # Too many quick movements
                    cheat_counter += 1

        # Eye aspect ratio for blink detection
        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)
        avg_ear = (left_ear + right_ear) / 2.0

        # Detect conscious avoidance (eyes open but not looking at screen)
        if avg_ear > EAR_THRESHOLD:
            # Check if eyes are looking at screen edges
            x_ratio = avg_center[0] / frame.shape[1]
            if x_ratio < 0.2 or x_ratio > 0.8:
                cheat_counter += 1

        # Detect gaze in specific regions
        if is_gaze_in_region(avg_center, QUESTION_REGION):
            if current_region != "QUESTION":
                current_region = "QUESTION"
                time_in_region = 0
                region_transitions.append("QUESTION")
            time_in_region += 1
        elif is_gaze_in_region(avg_center, ANSWER_REGION):
            if current_region != "ANSWER":
                current_region = "ANSWER"
                time_in_region = 0
                region_transitions.append("ANSWER")
            time_in_region += 1
        else:
            current_region = None
            time_in_region = 0

        # Detect suspicious pattern: QUESTION → ANSWER → QUESTION
        if len(region_transitions) >= 3:
            if (region_transitions[-3] == "QUESTION" and
                region_transitions[-2] == "ANSWER" and
                region_transitions[-1] == "QUESTION"):
                cheat_counter += 1
                cv2.putText(frame, "SUSPICIOUS PATTERN DETECTED!", (50, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        # Visual feedback
        cv2.rectangle(frame, (QUESTION_REGION[0], QUESTION_REGION[1]),
                      (QUESTION_REGION[2], QUESTION_REGION[3]), (0, 255, 0), 2)
        cv2.rectangle(frame, (ANSWER_REGION[0], ANSWER_REGION[1]),
                      (ANSWER_REGION[2], ANSWER_REGION[3]), (0, 0, 255), 2)
        cv2.circle(frame, avg_center, 5, (0, 255, 0), -1)
        cv2.putText(frame, f"Gaze Stability: {total_std:.1f}" if len(gaze_history) > 10 else "Calibrating...",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Cheating detection logic
        if cheat_counter > CONSECUTIVE_FRAMES:
            cheating_detected = True
            cv2.putText(frame, "CHEATING DETECTED!", (50, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            cheat_counter = CONSECUTIVE_FRAMES  # Prevent unlimited growth

    # Reset counter if no faces detected
    if len(faces) == 0:
        cheat_counter = max(0, cheat_counter - 2)

    # Show frame
    cv2.imshow("Anti-Cheating Monitor", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()