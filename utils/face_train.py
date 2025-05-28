import os
import cv2
import face_recognition
import pickle

DATASET_PATH = "face_dataset"
USER_ENCODINGS_FOLDER = "face_encodings"

def encode_faces_for_user(username):
    """
    Encode face images for a single user from face_dataset/username folder.
    Saves the encoding file as face_encodings/{username}_encodings.pickle.
    Returns True if successful, False otherwise.
    """
    user_folder = os.path.join(DATASET_PATH, username)
    if not os.path.isdir(user_folder):
        print(f"[ERROR] No folder found for user '{username}' in dataset.")
        return False

    known_encodings = []

    # Read images, encode faces
    for image_name in os.listdir(user_folder):
        image_path = os.path.join(user_folder, image_name)
        image = cv2.imread(image_path)
        if image is None:
            print(f"[WARNING] Unable to read image: {image_path}")
            continue

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, boxes)

        for encoding in encodings:
            known_encodings.append(encoding)

    if len(known_encodings) == 0:
        print("[ERROR] No faces found for encoding.")
        return False

    # Ensure folder exists
    os.makedirs(USER_ENCODINGS_FOLDER, exist_ok=True)

    # Save encodings to individual user file
    encoding_file_path = os.path.join(USER_ENCODINGS_FOLDER, f"{username}_encodings.pickle")
    with open(encoding_file_path, "wb") as f:
        pickle.dump({"encodings": known_encodings, "username": username}, f)

    print(f"[INFO] Encodings for '{username}' saved successfully at '{encoding_file_path}'.")
    return True


def save_encoding_info_to_db(username, encoding_file, mysql):
    encoding_file = f"face_encodings\\{username}_encodings.pickle"  # backslash path format
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO face_encodings (username, encoding_file)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE encoding_file = VALUES(encoding_file)
        """, (username, encoding_file))
        mysql.connection.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save encoding info to DB: {e}")
        return False



