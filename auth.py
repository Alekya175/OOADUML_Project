from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.database import db
from app.models import User
from app.utils.auth_helpers import get_current_user, login_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('customer.home'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        if not full_name or not username or not email or not password:
            flash('All required fields must be filled.', 'danger')
            return render_template('auth/register.html', full_name=full_name, username=username, email=email, phone=phone)

        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'danger')
            return render_template('auth/register.html', full_name=full_name, username=username, email=email, phone=phone)

        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/register.html', full_name=full_name, username=username, email=email, phone=phone)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html', full_name=full_name, username=username, email=email, phone=phone)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', full_name=full_name, username=username, email=email, phone=phone)

        # Check existing user
        if User.query.filter_by(username=username).first():
            flash('Username is already taken. Please choose another.', 'warning')
            return render_template('auth/register.html', full_name=full_name, email=email, phone=phone)

        if User.query.filter_by(email=email).first():
            flash('Email is already registered. Please log in.', 'warning')
            return render_template('auth/register.html', full_name=full_name, username=username, phone=phone)

        # Create customer user
        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            role='customer',
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in to reserve vehicles.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        user = get_current_user()
        if user and user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('customer.home'))

    next_url = request.args.get('next') or request.form.get('next')

    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '')

        if not login_id or not password:
            flash('Please provide both username/email and password.', 'danger')
            return render_template('auth/login.html', next=next_url)

        # Find user by username or email
        user = User.query.filter(
            (User.username == login_id.lower()) | (User.email == login_id.lower())
        ).first()

        if not user or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return render_template('auth/login.html', next=next_url)

        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'danger')
            return render_template('auth/login.html', next=next_url)

        # Establish session
        session.clear()
        session['user_id'] = user.id
        session['username'] = user.username
        session['full_name'] = user.full_name
        session['role'] = user.role

        flash(f'Welcome back, {user.full_name}!', 'success')

        if next_url and next_url.startswith('/'):
            return redirect(next_url)

        if user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('customer.home'))

    return render_template('auth/login.html', next=next_url)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('customer.home'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()

        if not full_name:
            flash('Full name cannot be blank.', 'danger')
        else:
            user.full_name = full_name
            user.phone = phone
            db.session.commit()
            session['full_name'] = full_name
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', user=user)
