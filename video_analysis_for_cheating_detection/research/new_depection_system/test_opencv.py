import cv2

print("Testing raw OpenCV webcam access...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Error: Webcam could not be opened.")
else:
    print("🟢 Webcam opened! Attempting to show window...")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Failed to grab frame.")
            break
            
        cv2.imshow("Raw Webcam Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    print("🏁 Test finished successfully.")
