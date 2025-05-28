import cv2
import os
import face_recognition
import geocoder
from datetime import datetime
from db_config import get_db_connection, get_db_cursor

def get_gps_location():
    g = geocoder.ip('me')
    if g.ok and g.latlng:
        return f"{g.latlng[0]}, {g.latlng[1]}"
    else:
        return "Unknown"

def capture_faces(username, num_pics=5):
    folder = f"face_dataset/{username}"
    os.makedirs(folder, exist_ok=True)

    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        print("Error: Could not open webcam.")
        return None

    count = 0
    while count < num_pics:
        ret, frame = video_capture.read()
        if not ret:
            break

        rgb_frame = frame[:, :, ::-1]
        face_locations = face_recognition.face_locations(rgb_frame)

        if face_locations:
            img_path = os.path.join(folder, f"{username}_{count + 1}.jpg")
            cv2.imwrite(img_path, frame)
            count += 1
            print(f"Captured {count}/{num_pics}")
        else:
            print("Face not detected.")

        cv2.imshow("Capturing Face (press 'q' to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

    return folder if count > 0 else None

def save_location_to_db(username, location, status="Registered"):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO attendance_logs (username, date, time, gps_location, status) VALUES (%s, %s, %s, %s, %s)",
        (username, date, time, location, status)
    )
    db.commit()
    cursor.close()
    db.close()
