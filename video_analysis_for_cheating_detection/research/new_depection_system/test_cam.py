import cv2
import time
from computer_vision import CheatingDetection

def main():
    print("==================================================")
    print("Initializing Anti-Cheating System Test Dashboard...")
    print("==================================================")
    
    try:
        print("DEBUG: Instantiating CheatingDetection...")
        detector = CheatingDetection()
        print("DEBUG: CheatingDetection instantiated successfully.")
    except Exception as e:
        print(f"❌ Error during CheatingDetection init: {e}")
        import traceback
        traceback.print_exc()
        return

    try:
        print("DEBUG: Opening native webcam (cv2.VideoCapture(0))...")
        cap = cv2.VideoCapture(0)
        print("DEBUG: VideoCapture call executed.")
    except Exception as e:
        print(f"❌ Error during cv2.VideoCapture: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if not cap.isOpened():
        print("❌ Error: Could not open native webcam. Please check permissions.")
        return
        
    print("\n🟢 Webcam active! Launching local visual testing window...")
    print("👉 Press 'q' inside the video window to quit.\n")
    
    warning_count = 0
    disqualified = False

    
    # Simple evaluation loop
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Failed to grab frame.")
            break
            
        # Analyze using your ML core
        violations, output_frame = detector.detect_cheating(frame)
        
        # Increment warnings if anything is triggered
        active_violations = [k for k, v in violations.items() if v]
        if active_violations and not disqualified:
            warning_count += 1
            if warning_count >= 100:  # e.g., ~3-5 seconds of sustained violations
                disqualified = True
                
        # Draw live status summary
        if disqualified:
            cv2.putText(output_frame, "STATUS: DISQUALIFIED ❌", (20, output_frame.shape[0] - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
        else:
            status_text = f"Warnings: {warning_count}/100"
            cv2.putText(output_frame, f"STATUS: OK | {status_text}", (20, output_frame.shape[0] - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        
        # Display
        cv2.imshow("Live Anti-Cheating Core Evaluation", output_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    print("\n🏁 Test concluded safely.")

if __name__ == "__main__":
    main()
