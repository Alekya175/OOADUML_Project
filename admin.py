from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import db
from app.models import Vehicle, Booking, Payment, User
from app.utils.auth_helpers import admin_required, get_current_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_vehicles = Vehicle.query.count()
    available_vehicles = Vehicle.query.filter_by(status='available').count()
    rented_vehicles = Vehicle.query.filter_by(status='rented').count()
    maintenance_vehicles = Vehicle.query.filter_by(status='maintenance').count()
    two_wheelers_count = Vehicle.query.filter_by(category='2 Wheeler').count()
    four_wheelers_count = Vehicle.query.filter_by(category='4 Wheeler').count()

    total_bookings = Booking.query.count()
    confirmed_bookings = Booking.query.filter_by(status='confirmed').count()
    pending_bookings = Booking.query.filter_by(status='pending_payment').count()
    completed_bookings = Booking.query.filter_by(status='completed').count()
    cancelled_bookings = Booking.query.filter_by(status='cancelled').count()

    total_customers = User.query.filter_by(role='customer').count()

    # Total revenue from completed payments
    revenue_sum = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'completed').scalar() or 0.0

    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(8).all()

    return render_template(
        'admin/dashboard.html',
        total_vehicles=total_vehicles,
        two_wheelers_count=two_wheelers_count,
        four_wheelers_count=four_wheelers_count,
        available_vehicles=available_vehicles,
        rented_vehicles=rented_vehicles,
        maintenance_vehicles=maintenance_vehicles,
        total_bookings=total_bookings,
        confirmed_bookings=confirmed_bookings,
        pending_bookings=pending_bookings,
        completed_bookings=completed_bookings,
        cancelled_bookings=cancelled_bookings,
        total_customers=total_customers,
        total_revenue=float(revenue_sum),
        recent_bookings=recent_bookings,
        recent_payments=recent_payments
    )


# --- Vehicle Management ---

@admin_bp.route('/vehicles')
@admin_required
def vehicles():
    query_text = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
    category = request.args.get('category', '').strip()
    v_type = request.args.get('type', '').strip()

    vehicles_query = Vehicle.query

    if query_text:
        term = f"%{query_text}%"
        vehicles_query = vehicles_query.filter(
            (Vehicle.name.ilike(term)) | (Vehicle.make.ilike(term)) | (Vehicle.location.ilike(term))
        )
    if status:
        vehicles_query = vehicles_query.filter(Vehicle.status == status)
    if category:
        vehicles_query = vehicles_query.filter(Vehicle.category == category)
    if v_type:
        vehicles_query = vehicles_query.filter(Vehicle.vehicle_type == v_type)

    all_vehicles = vehicles_query.order_by(Vehicle.id.desc()).all()
    types = [t[0] for t in db.session.query(Vehicle.vehicle_type).distinct().all() if t[0]]
    categories = ['2 Wheeler', '4 Wheeler']

    return render_template(
        'admin/vehicles.html',
        vehicles=all_vehicles,
        types=types,
        categories=categories,
        selected_category=category,
        selected_status=status,
        selected_type=v_type,
        query_text=query_text
    )


@admin_bp.route('/vehicles/new', methods=['GET', 'POST'])
@admin_required
def add_vehicle():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        make = request.form.get('make', '').strip()
        model = request.form.get('model', '').strip()
        year_str = request.form.get('year', '').strip()
        category = request.form.get('category', '4 Wheeler').strip()
        vehicle_type = request.form.get('vehicle_type', '').strip()
        location = request.form.get('location', '').strip()
        daily_rate_str = request.form.get('daily_rate', '').strip()
        seating_str = request.form.get('seating_capacity', '2' if category == '2 Wheeler' else '5').strip()
        transmission = request.form.get('transmission', 'Automatic').strip()
        fuel_type = request.form.get('fuel_type', 'Petrol').strip()
        mileage = request.form.get('mileage', 'Unlimited').strip()
        image_url = request.form.get('image_url', '').strip()
        description = request.form.get('description', '').strip()
        features = request.form.get('features', '').strip()
        status = request.form.get('status', 'available').strip()

        # Validation
        if not name or not make or not model or not daily_rate_str or not location:
            flash('Name, Make, Model, Daily Rate, and Location are required.', 'danger')
            return render_template('admin/vehicle_form.html', vehicle=None, action='Add')

        try:
            daily_rate = Decimal(daily_rate_str)
            if daily_rate <= 0:
                raise ValueError
        except (ValueError, TypeError):
            flash('Daily rate must be a positive number in Rupees (₹).', 'danger')
            return render_template('admin/vehicle_form.html', vehicle=None, action='Add')

        try:
            year = int(year_str)
            seating = int(seating_str)
        except (ValueError, TypeError):
            flash('Year and Seating Capacity must be valid integers.', 'danger')
            return render_template('admin/vehicle_form.html', vehicle=None, action='Add')

        default_img = '/static/images/cruiser_bike.jpg' if category == '2 Wheeler' else '/static/images/luxury_sedan.jpg'
        new_vehicle = Vehicle(
            name=name,
            make=make,
            model=model,
            year=year,
            category=category,
            vehicle_type=vehicle_type or ('Cruiser' if category == '2 Wheeler' else 'Sedan'),
            location=location,
            daily_rate=daily_rate,
            seating_capacity=seating,
            transmission=transmission,
            fuel_type=fuel_type,
            mileage=mileage,
            image_url=image_url or default_img,
            description=description,
            features=features,
            status=status
        )

        db.session.add(new_vehicle)
        db.session.commit()

        flash(f'Vehicle "{name}" has been successfully added to the fleet.', 'success')
        return redirect(url_for('admin.vehicles'))

    return render_template('admin/vehicle_form.html', vehicle=None, action='Add')


@admin_bp.route('/vehicles/<int:vehicle_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        make = request.form.get('make', '').strip()
        model = request.form.get('model', '').strip()
        year_str = request.form.get('year', '').strip()
        category = request.form.get('category', vehicle.category or '4 Wheeler').strip()
        vehicle_type = request.form.get('vehicle_type', '').strip()
        location = request.form.get('location', '').strip()
        daily_rate_str = request.form.get('daily_rate', '').strip()
        seating_str = request.form.get('seating_capacity', '5').strip()
        transmission = request.form.get('transmission', 'Automatic').strip()
        fuel_type = request.form.get('fuel_type', 'Petrol').strip()
        mileage = request.form.get('mileage', 'Unlimited').strip()
        image_url = request.form.get('image_url', '').strip()
        description = request.form.get('description', '').strip()
        features = request.form.get('features', '').strip()
        status = request.form.get('status', 'available').strip()

        if not name or not make or not model or not daily_rate_str or not location:
            flash('Name, Make, Model, Daily Rate, and Location are required.', 'danger')
            return render_template('admin/vehicle_form.html', vehicle=vehicle, action='Edit')

        try:
            daily_rate = Decimal(daily_rate_str)
            year = int(year_str)
            seating = int(seating_str)
        except (ValueError, TypeError):
            flash('Please enter valid numeric values for rate, year, and seating.', 'danger')
            return render_template('admin/vehicle_form.html', vehicle=vehicle, action='Edit')

        vehicle.name = name
        vehicle.make = make
        vehicle.model = model
        vehicle.year = year
        vehicle.category = category
        vehicle.vehicle_type = vehicle_type
        vehicle.location = location
        vehicle.daily_rate = daily_rate
        vehicle.seating_capacity = seating
        vehicle.transmission = transmission
        vehicle.fuel_type = fuel_type
        vehicle.mileage = mileage
        if image_url:
            vehicle.image_url = image_url
        vehicle.description = description
        vehicle.features = features
        vehicle.status = status

        db.session.commit()
        flash(f'Vehicle "{vehicle.name}" updated successfully.', 'success')
        return redirect(url_for('admin.vehicles'))

    return render_template('admin/vehicle_form.html', vehicle=vehicle, action='Edit')


@admin_bp.route('/vehicles/<int:vehicle_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_vehicle_status(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    new_status = request.form.get('status')
    if new_status in ['available', 'maintenance', 'rented', 'inactive']:
        vehicle.status = new_status
        db.session.commit()
        flash(f'Vehicle status changed to {new_status}.', 'success')
    return redirect(url_for('admin.vehicles'))


# --- Booking Management ---

@admin_bp.route('/bookings')
@admin_required
def bookings():
    status = request.args.get('status', '').strip()
    query_text = request.args.get('q', '').strip()

    bookings_query = Booking.query

    if status:
        bookings_query = bookings_query.filter(Booking.status == status)

    if query_text:
        term = f"%{query_text}%"
        bookings_query = bookings_query.join(User).join(Vehicle).filter(
            (Booking.booking_reference.ilike(term)) |
            (User.full_name.ilike(term)) |
            (User.email.ilike(term)) |
            (Vehicle.name.ilike(term))
        )

    all_bookings = bookings_query.order_by(Booking.created_at.desc()).all()
    return render_template(
        'admin/bookings.html',
        bookings=all_bookings,
        selected_status=status,
        query_text=query_text
    )


@admin_bp.route('/bookings/<int:booking_id>/update-status', methods=['POST'])
@admin_required
def update_booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get('status')

    valid_statuses = ['pending_payment', 'confirmed', 'completed', 'cancelled']
    if new_status in valid_statuses:
        booking.status = new_status
        if new_status == 'cancelled':
            booking.cancellation_reason = request.form.get('reason', 'Cancelled by administrator')
            booking.cancelled_at = datetime.utcnow()
            # If payment was completed, refund it
            payment = booking.latest_payment()
            if payment and payment.status == 'completed':
                payment.status = 'refunded'
        db.session.commit()
        flash(f'Booking #{booking.booking_reference} status updated to "{new_status}".', 'success')
    else:
        flash('Invalid booking status provided.', 'danger')

    return redirect(url_for('admin.bookings'))


# --- Customer Records ---

@admin_bp.route('/customers')
@admin_required
def customers():
    all_customers = User.query.filter_by(role='customer').order_by(User.created_at.desc()).all()
    return render_template('admin/customers.html', customers=all_customers)


# --- Payment Records ---

@admin_bp.route('/payments')
@admin_required
def payments():
    status = request.args.get('status', '').strip()
    payments_query = Payment.query

    if status:
        payments_query = payments_query.filter(Payment.status == status)

    all_payments = payments_query.order_by(Payment.created_at.desc()).all()
    return render_template('admin/payments.html', payments=all_payments, selected_status=status)
