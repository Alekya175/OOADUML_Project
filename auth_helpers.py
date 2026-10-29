from functools import wraps
from flask import session, redirect, url_for, flash, request
from app.database import db
from app.models import User

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return db.session.get(User, user_id)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Admin authentication required.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        user = get_current_user()
        if not user or not user.is_admin():
            flash('Access denied: Administrator privileges required.', 'danger')
            return redirect(url_for('customer.home'))
        return f(*args, **kwargs)
    return decorated_function
