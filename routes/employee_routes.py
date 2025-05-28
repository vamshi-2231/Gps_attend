import datetime
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session
from app import mysql
from db_config import get_db_connection
from utils.face_recognizer import recognize_face
from utils.helpers import login_required
from utils.gps_utils import is_within_range

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')

@employee_bp.route('/dashboard')
@login_required(role='employee')
def dashboard():
    return render_template('employee/emp_dashboard.html')

# ─────────────────────────────
# LEAVE REQUEST
# ─────────────────────────────

@employee_bp.route('/leave-request', methods=['GET', 'POST'])
@login_required(role='employee')
def leave_request():
    username = session.get('username')  # assuming you store username in session during login
    if not username:
        flash("User not logged in.", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        leave_type = request.form['leave_type']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']

        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO leaves (username, leave_type, start_date, end_date, reason, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, leave_type, start_date, end_date, reason, 'Pending'))
            mysql.connection.commit()
            flash("Leave request submitted successfully.", "success")
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error submitting leave request: {e}", "danger")
        finally:
            cur.close()

        return redirect(url_for('employee.leave_request'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM leaves WHERE username = %s ORDER BY start_date DESC", (username,))
    leaves = cur.fetchall()
    cur.close()
    return render_template('employee/leave_request.html', leaves=leaves)


# ─────────────────────────────
# VIEW ATTENDDENCE
# ─────────────────────────────

@employee_bp.route('/view-attendance')
@login_required(role='employee')
def view_attendance():
    username = session.get('username')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM attendance_logs WHERE username = %s ORDER BY date DESC", (username,))
    logs = cursor.fetchall()
    cursor.close()

    return render_template('employee/view_attendance.html', logs=logs)

# ─────────────────────────────
# MARK ATTENDENCE
# ─────────────────────────────
@employee_bp.route('/mark_attendance', methods=['GET'])
@login_required(role='employee')
def mark_attendance():
    return render_template('employee/mark_attendance.html')

