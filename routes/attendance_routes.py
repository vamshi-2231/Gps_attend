from flask import Blueprint, render_template, request, session, redirect, url_for
import os
import pickle
import face_recognition
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import numpy as np
from db_config import mysql

attendance_bp = Blueprint('attendance', __name__, template_folder='../templates')


@attendance_bp.route('/employee/mark_attendance', methods=['GET'])
def mark_attendance_page():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    return render_template('employee/mark_attendance.html')


@attendance_bp.route('/mark_attendance_submit', methods=['POST'])
def mark_attendance_submit():
    filepath = None  # Define outside try block for safe deletion in case of error
    try:
        if 'username' not in session:
            return 'Unauthorized', 401

        username = session['username']

        if 'face_image' not in request.files:
            return 'No face image provided', 400

        face_file = request.files['face_image']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        if not (latitude and longitude):
            return 'Location not provided', 400

        # Save uploaded image temporarily
        os.makedirs('temp', exist_ok=True)
        filepath = os.path.join('temp', secure_filename('temp_face.jpg'))
        face_file.save(filepath)

        # Detect face and extract encoding
        img = face_recognition.load_image_file(filepath)
        face_locations = face_recognition.face_locations(img)
        face_encodings = face_recognition.face_encodings(img, face_locations)

        if not face_encodings:
            os.remove(filepath)
            return 'No face detected in the image', 400

        # Load known encodings
        encoding_path = os.path.join('face_encodings', f'{username}_encodings.pickle')

        if not os.path.exists(encoding_path):
            os.remove(filepath)
            return 'Encoding file not found', 404

        with open(encoding_path, 'rb') as f:
            data = pickle.load(f)

        # ✅ Fixed: Load the encodings properly
        known_encodings = data.get("encodings", [])

        if not known_encodings:
            os.remove(filepath)
            return 'No valid face encodings found', 500

        # Compare encodings
        matches = face_recognition.compare_faces(known_encodings, face_encodings[0])

        if not any(matches):
            os.remove(filepath)
            return 'Face not recognized', 401

        now = datetime.now()
        today = now.date()
        current_time = now.time()
        gps_location = f"{latitude},{longitude}"

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM attendance_logs WHERE username = %s AND date = %s", (username, today))
        record = cursor.fetchone()

        if not record:
            cursor.execute("""
                INSERT INTO attendance_logs (username, date, login_time, login_location)
                VALUES (%s, %s, %s, %s)
            """, (username, today, current_time, gps_location))
            mysql.connection.commit()
            message = f"✅ Login marked at {current_time.strftime('%H:%M:%S')}"
        else:
            if record['logout_time'] is not None:
                cursor.close()
                os.remove(filepath)
                return "❌ Already logged out today.", 400

            login_time_obj = record['login_time']
            if isinstance(login_time_obj, timedelta):
                login_time_obj = (datetime.min + login_time_obj).time()

            login_datetime = datetime.combine(today, login_time_obj)
            time_diff = (now - login_datetime).total_seconds()

            if time_diff < 3600:
                cursor.close()
                os.remove(filepath)
                return "⏳ Logout only allowed after 1 hour of login.", 400

            cursor.execute("""
                UPDATE attendance_logs
                SET logout_time = %s, logout_location = %s
                WHERE id = %s
            """, (current_time, gps_location, record['id']))
            mysql.connection.commit()
            message = f"✅ Logout marked at {current_time.strftime('%H:%M:%S')}"

        cursor.close()
        os.remove(filepath)
        return message

    except Exception as e:
        import traceback
        traceback.print_exc()
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return f"Error: {str(e)}", 500
