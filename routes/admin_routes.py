import os
from flask import Blueprint, render_template, request, redirect, flash, url_for
from db_config import mysql
from utils.face_train import encode_faces_for_user, save_encoding_info_to_db
from utils.face_capture import capture_faces
from utils.helpers import login_required
from utils.face_recognizer import recognize_face

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required(role='admin')
def dashboard():
    return render_template('admin/admin_dashboard.html')

# ─────────────────────────────
# MANAGE EMPLOYEES
# ─────────────────────────────

@admin_bp.route('/employees')
@login_required(role='admin')
def list_employees():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT e.id, e.first_name, e.last_name, e.position, e.phone, e.username,
               u.password
        FROM employees e
        LEFT JOIN users u ON e.username = u.username
    """)
    employees = cur.fetchall()
    cur.close()
    return render_template('admin/Manage_emp.html', employees=employees)

@admin_bp.route('/add_employee', methods=['GET', 'POST'])
@login_required(role='admin')
def add_employee():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        position = request.form['position']
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()

        # Insert employee
        cur.execute("""
            INSERT INTO employees (first_name, last_name, position, phone, username)
            VALUES (%s, %s, %s, %s, %s)
        """, (first_name, last_name, position, phone, username))

        # Insert user
        cur.execute("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, 'employee')
        """, (username, password))

        mysql.connection.commit()
        cur.close()
        flash('Employee and user account created successfully', 'success')
        return redirect(url_for('admin.list_employees'))

    return render_template('admin/Manage_emp.html')

@admin_bp.route('/edit_employee/<int:id>', methods=['POST'])
@login_required(role='admin')
def edit_employee(id):
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    position = request.form['position']
    phone = request.form['phone']

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE employees
        SET first_name=%s, last_name=%s, position=%s, phone=%s
        WHERE id=%s
    """, (first_name, last_name, position, phone, id))
    mysql.connection.commit()
    cur.close()
    flash('Employee updated successfully', 'success')
    return redirect(url_for('admin.list_employees'))

@admin_bp.route('/edit_user/<username>', methods=['POST'])
@login_required(role='admin')
def edit_user(username):
    new_username = request.form['username']
    new_password = request.form['password']

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE users SET username=%s, password=%s WHERE username=%s
    """, (new_username, new_password, username))

    cur.execute("""
        UPDATE employees SET username=%s WHERE username=%s
    """, (new_username, username))

    mysql.connection.commit()
    cur.close()
    flash('User credentials updated successfully', 'success')
    return redirect(url_for('admin.list_employees'))

@admin_bp.route('/delete_employee/<int:id>', methods=['POST'])
@login_required(role='admin')
def delete_employee(id):
    cur = mysql.connection.cursor()

    cur.execute("SELECT username FROM employees WHERE id=%s", (id,))
    result = cur.fetchone()
    if result:
        username = result['username']
        cur.execute("DELETE FROM users WHERE username=%s", (username,))

    cur.execute("DELETE FROM employees WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()

    flash('Employee and user account deleted successfully', 'success')
    return redirect(url_for('admin.list_employees'))

@admin_bp.route('/delete_user/<username>', methods=['POST'])
@login_required(role='admin')
def delete_user(username):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE username=%s", (username,))
    mysql.connection.commit()
    cur.close()
    flash(f"User {username} deleted successfully", "success")
    return redirect(url_for('admin.list_employees'))


# ───────────────────────────────────
# FACE CAPTURE & TRAINING & VERIFY
# ───────────────────────────────────

@admin_bp.route('/manage_faces', methods=['GET', 'POST'])
@login_required(role='admin')
def manage_faces():
    message = None
    usernames = []

    try:
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role = 'employee'")
        result = cursor.fetchall()
        usernames = [row['username'] for row in result]
        cursor.close()
    except Exception as e:
        message = f"❌ Error fetching usernames: {str(e)}"
        usernames = []

    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username')

        if not username:
            message = "⚠️ Username is required."
        else:
            if action == 'capture':
                folder = capture_faces(username)
                if folder:
                    message = f"✅ Face images captured for {username}."
                else:
                    message = f"❌ Face capture failed for {username}."

            elif action == 'train':
                success = encode_faces_for_user(username)
                if success:
                    encoding_file_path = os.path.join("encodings", "faces_data.pickle")
                    saved = save_encoding_info_to_db(username, encoding_file_path, mysql)
                    if saved:
                        message = f"✅ Face encodings trained and saved for {username}."
                    else:
                        message = f"❌ Failed to save encoding info to DB for {username}."
                else:
                    message = f"❌ Face training failed for {username}."

    return render_template('admin/Manage_faces.html', message=message, usernames=usernames)

# ───────────────────────────────────
#    VERIFY
# ───────────────────────────────────
@admin_bp.route('/verify_face', methods=['POST'])
@login_required(role='admin')
def verify_face():
    username = request.form.get('username')
    if not username:
        flash("⚠️ Username is required for verification.", "warning")
        return redirect(url_for('admin.manage_faces'))

    recognized_user = recognize_face(employee_id=username)

    if recognized_user == username:
        message = f"✅ Face verification succeeded for {username}!"
    else:
        message = f"❌ Face verification failed for {username}."

    # Re-fetch usernames for dropdown
    try:
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role = 'employee'")
        result = cursor.fetchall()
        usernames = [row['username'] for row in result]
        cursor.close()
    except Exception as e:
        usernames = []
        message += f" (Also failed to fetch usernames: {e})"

    return render_template('admin/Manage_faces.html', message=message, usernames=usernames)


# ─────────────────────────────
# LOCATION MANAGEMENT
# ─────────────────────────────
@admin_bp.route('/locations', methods=['GET', 'POST'])
@login_required(role='admin')
def manage_locations():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        place = request.form['place']
        city = request.form['city']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        cur.execute(
            "INSERT INTO locations (place, city, latitude, longitude) VALUES (%s, %s, %s, %s)",
            (place, city, latitude, longitude)
        )
        mysql.connection.commit()
        flash('Location added successfully')

    cur.execute("SELECT * FROM locations")
    locations = cur.fetchall()
    cur.close()

    return render_template('admin/locations.html', locations=locations)

# ─────────────────────────────
# VIEW ATTENDANCE LOGS
# ─────────────────────────────
@admin_bp.route('/admin/attendance_logs')
@login_required(role='admin')
def attendance_logs():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, username, date, login_time, logout_time, login_location, logout_location
        FROM attendance_logs
        ORDER BY date DESC, login_time DESC
    """)
    logs = cur.fetchall()
    cur.close()
    return render_template('admin/attendance_logs.html', logs=logs)

# ─────────────────────────────
# VIEW all leave requests
# ─────────────────────────────

@admin_bp.route('/leaves')
@login_required(role='admin')
def view_leaves():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, username, leave_type, start_date, end_date, reason, status
        FROM leaves
        ORDER BY start_date DESC
    """)
    leaves = cur.fetchall()
    cur.close()
    return render_template('admin/Manage_leaves.html', leaves=leaves)

# Approve leave
@admin_bp.route('/leaves/approve/<int:leave_id>')
@login_required(role='admin')
def approve_leave(leave_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE leaves SET status='Approved' WHERE id=%s", (leave_id,))
    mysql.connection.commit()
    cur.close()
    flash("Leave Approved", "success")
    return redirect(url_for('admin.view_leaves'))

# Reject leave
@admin_bp.route('/leaves/reject/<int:leave_id>')
@login_required(role='admin')
def reject_leave(leave_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE leaves SET status='Rejected' WHERE id=%s", (leave_id,))
    mysql.connection.commit()
    cur.close()
    flash("Leave Rejected", "danger")
    return redirect(url_for('admin.view_leaves'))