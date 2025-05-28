from functools import wraps
from flask import session, redirect, url_for

def login_required(role=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))  # your login route
            if role and session.get('role') != role:
                return redirect(url_for('auth.login'))  # or maybe redirect to 'unauthorized' page
            return func(*args, **kwargs)
        return wrapper
    return decorator  # <--- This is required!
