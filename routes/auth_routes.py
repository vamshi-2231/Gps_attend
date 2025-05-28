from flask import Blueprint, flash, request, render_template, redirect, url_for, session
from db_config import mysql  # MySQL connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']  # <-- store username here
            session['role'] = user['role']

            if user['role'] == 'admin':
                return redirect('/admin/dashboard')
            else:
                return redirect('/employee/dashboard')
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')
