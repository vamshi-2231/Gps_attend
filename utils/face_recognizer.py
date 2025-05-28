import cv2
import face_recognition
import pickle
import numpy as np
import os
import time  # To handle timeout

ENCODINGS_DIR = "face_encodings"

def recognize_face(employee_id=None, timeout=10):
    print("[INFO] Starting face recognition...")

    known_encodings = []
    known_ids = []

    # Load all .pickle files in the encoding directory
    for filename in os.listdir(ENCODINGS_DIR):
        if filename.endswith(".pickle"):
            filepath = os.path.join(ENCODINGS_DIR, filename)
            with open(filepath, "rb") as f:
                data = pickle.load(f)
                known_encodings.extend(data["encodings"])
                known_ids.extend([data["username"]] * len(data["encodings"]))

    if not known_encodings:
        print("[ERROR] No face encodings found.")
        return None

    cap = cv2.VideoCapture(0)
    recognized_id = None

    start_time = time.time()  # Start timer

    while True:
        if time.time() - start_time > timeout:
            print("[INFO] Timeout reached. Face not recognized.")
            break

        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to capture frame from camera.")
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, boxes)

        for encoding in encodings:
            matches = face_recognition.compare_faces(known_encodings, encoding)
            face_distances = face_recognition.face_distance(known_encodings, encoding)

            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    recognized_id = known_ids[best_match_index]
                    print(f"[INFO] Recognized: {recognized_id}")

                    # Check if matched with the selected employee
                    if employee_id and recognized_id != employee_id:
                        print("[WARNING] Face does not match selected employee.")
                        continue

                    cap.release()
                    cv2.destroyAllWindows()
                    return recognized_id

        # Show live preview
        cv2.imshow("Face Verification (Press Q to Quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] Manual exit triggered.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return None
