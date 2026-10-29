from datetime import date, datetime, timezone
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort
from app.database import db
from app.models import Vehicle, Booking, Payment, User
from app.utils.auth_helpers import get_current_user, login_required
from app.utils.booking_helpers import (
    parse_date, 
    calculate_rental_quote, 
    generate_booking_reference, 
    generate_payment_reference, 
    generate_simulated_transaction_id
)

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
def home():
    featured_vehicles = Vehicle.query.filter_by(status='available').limit(8).all()
    two_wheelers = Vehicle.query.filter_by(status='available', category='2 Wheeler').limit(4).all()
    four_wheelers = Vehicle.query.filter_by(status='available', category='4 Wheeler').limit(4).all()
    locations = [loc[0] for loc in db.session.query(Vehicle.location).distinct().all() if loc[0]]
    vehicle_types = [t[0] for t in db.session.query(Vehicle.vehicle_type).distinct().all() if t[0]]
    categories = ['2 Wheeler', '4 Wheeler']
    return render_template(
        'index.html',
        featured_vehicles=featured_vehicles,
        two_wheelers=two_wheelers,
        four_wheelers=four_wheelers,
        locations=locations,
        vehicle_types=vehicle_types,
        categories=categories,
        today=date.today().isoformat()
    )


@customer_bp.route('/vehicles')
def catalog():
    query_text = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    v_type = request.args.get('type', '').strip()
    location = request.args.get('location', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()
    transmission = request.args.get('transmission', '').strip()
    fuel = request.args.get('fuel', '').strip()
    sort_by = request.args.get('sort', 'price_asc')
    pickup_str = request.args.get('pickup_date', '').strip()
    return_str = request.args.get('return_date', '').strip()

    vehicles_query = Vehicle.query.filter(Vehicle.status != 'inactive')

    if query_text:
        search_filter = f"%{query_text}%"
        vehicles_query = vehicles_query.filter(
            (Vehicle.name.ilike(search_filter)) |
            (Vehicle.make.ilike(search_filter)) |
            (Vehicle.model.ilike(search_filter)) |
            (Vehicle.description.ilike(search_filter)) |
            (Vehicle.location.ilike(search_filter))
        )

    if category:
        vehicles_query = vehicles_query.filter(Vehicle.category == category)

    if v_type:
        vehicles_query = vehicles_query.filter(Vehicle.vehicle_type == v_type)

    if location:
        vehicles_query = vehicles_query.filter(Vehicle.location == location)

    if transmission:
        vehicles_query = vehicles_query.filter(Vehicle.transmission == transmission)

    if fuel:
        vehicles_query = vehicles_query.filter(Vehicle.fuel_type == fuel)

    if min_price:
        try:
            vehicles_query = vehicles_query.filter(Vehicle.daily_rate >= float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            vehicles_query = vehicles_query.filter(Vehicle.daily_rate <= float(max_price))
        except ValueError:
            pass

    # Sort
    if sort_by == 'price_desc':
        vehicles_query = vehicles_query.order_by(Vehicle.daily_rate.desc())
    elif sort_by == 'year_desc':
        vehicles_query = vehicles_query.order_by(Vehicle.year.desc())
    elif sort_by == 'name_asc':
        vehicles_query = vehicles_query.order_by(Vehicle.name.asc())
    else:
        vehicles_query = vehicles_query.order_by(Vehicle.daily_rate.asc())

    all_vehicles = vehicles_query.all()

    # Filter by date availability if both dates provided
    pickup_date = parse_date(pickup_str)
    return_date = parse_date(return_str)
    date_filter_active = False

    if pickup_date and return_date and return_date > pickup_date:
        date_filter_active = True
        available_vehicles = [
            v for v in all_vehicles if v.is_available_for_dates(pickup_date, return_date)
        ]
    else:
        available_vehicles = all_vehicles

    distinct_types = [t[0] for t in db.session.query(Vehicle.vehicle_type).distinct().all() if t[0]]
    distinct_locations = [l[0] for l in db.session.query(Vehicle.location).distinct().all() if l[0]]
    distinct_categories = ['2 Wheeler', '4 Wheeler']

    # Total counts for tab filters
    total_all = Vehicle.query.filter(Vehicle.status != 'inactive').count()
    total_2w = Vehicle.query.filter(Vehicle.status != 'inactive', Vehicle.category == '2 Wheeler').count()
    total_4w = Vehicle.query.filter(Vehicle.status != 'inactive', Vehicle.category == '4 Wheeler').count()

    return render_template(
        'vehicles/catalog.html',
        vehicles=available_vehicles,
        total_count=len(available_vehicles),
        types=distinct_types,
        locations=distinct_locations,
        categories=distinct_categories,
        category_counts={'all': total_all, '2w': total_2w, '4w': total_4w, 'two_w': total_2w, 'four_w': total_4w},
        selected_category=category,
        selected_type=v_type,
        selected_location=location,
        selected_transmission=transmission,
        selected_fuel=fuel,
        query_text=query_text,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        pickup_date=pickup_str,
        return_date=return_str,
        date_filter_active=date_filter_active,
        today=date.today().isoformat()
    )


@customer_bp.route('/vehicles/<int:vehicle_id>')
def vehicle_detail(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if vehicle.status == 'inactive':
        flash('This vehicle is currently not in active service.', 'warning')
        return redirect(url_for('customer.catalog'))

    pickup_str = request.args.get('pickup_date', '')
    return_str = request.args.get('return_date', '')

    pickup_date = parse_date(pickup_str)
    return_date = parse_date(return_str)
    quote = None

    if pickup_date and return_date:
        quote = calculate_rental_quote(vehicle.daily_rate, pickup_date, return_date)
        if quote['valid']:
            quote['is_available'] = vehicle.is_available_for_dates(pickup_date, return_date)

    return render_template(
        'vehicles/detail.html',
        vehicle=vehicle,
        pickup_date=pickup_str,
        return_date=return_str,
        quote=quote,
        today=date.today().isoformat()
    )


@customer_bp.route('/book/<int:vehicle_id>', methods=['POST'])
@login_required
def create_booking(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    user = get_current_user()

    if vehicle.status != 'available':
        flash('Sorry, this vehicle is currently not available for new reservations.', 'danger')
        return redirect(url_for('customer.vehicle_detail', vehicle_id=vehicle.id))

    pickup_str = request.form.get('pickup_date', '').strip()
    return_str = request.form.get('return_date', '').strip()
    notes = request.form.get('notes', '').strip()

    pickup_date = parse_date(pickup_str)
    return_date = parse_date(return_str)

    # 1. Booking rule validation: return date strictly after pickup date
    quote = calculate_rental_quote(vehicle.daily_rate, pickup_date, return_date)
    if not quote['valid']:
        flash(quote['error'], 'danger')
        return redirect(url_for('customer.vehicle_detail', vehicle_id=vehicle.id, pickup_date=pickup_str, return_date=return_str))

    # 2. Strict availability conflict check: no overlapping confirmed/pending bookings
    if not vehicle.is_available_for_dates(pickup_date, return_date):
        flash('The selected vehicle is already reserved for these dates. Please choose different dates or another vehicle.', 'warning')
        return redirect(url_for('customer.vehicle_detail', vehicle_id=vehicle.id, pickup_date=pickup_str, return_date=return_str))

    # 3. Create booking
    booking = Booking(
        booking_reference=generate_booking_reference(),
        user_id=user.id,
        vehicle_id=vehicle.id,
        pickup_date=pickup_date,
        return_date=return_date,
        total_days=quote['days'],
        daily_rate=quote['daily_rate'],
        subtotal_amount=quote['subtotal'],
        tax_amount=quote['tax'],
        total_amount=quote['total'],
        status='pending_payment',
        notes=notes
    )

    db.session.add(booking)
    db.session.commit()

    flash('Reservation initiated! Please complete your simulated payment to confirm your booking.', 'info')
    return redirect(url_for('customer.checkout', booking_ref=booking.booking_reference))


@customer_bp.route('/checkout/<booking_ref>', methods=['GET', 'POST'])
@login_required
def checkout(booking_ref):
    booking = Booking.query.filter_by(booking_reference=booking_ref).first_or_404()
    user = get_current_user()

    # Authorization check
    if booking.user_id != user.id and not user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.home'))

    # If already confirmed
    if booking.status == 'confirmed':
        flash('This reservation is already confirmed and paid.', 'info')
        return redirect(url_for('customer.booking_confirmation', booking_ref=booking.booking_reference))

    if booking.status == 'cancelled':
        flash('This booking was cancelled and cannot be paid for.', 'warning')
        return redirect(url_for('customer.booking_history'))

    if request.method == 'POST':
        # Simulated payment submission supporting Indian payment methods
        payment_mode = request.form.get('payment_mode', 'card') # 'upi', 'card', 'netbanking', 'hub'
        payment_method = request.form.get('payment_method', '')
        cardholder_name = request.form.get('cardholder_name', user.full_name).strip()
        card_number = request.form.get('card_number', '').replace(' ', '').strip()
        upi_id = request.form.get('upi_id', '').strip()
        bank_name = request.form.get('bank_name', 'HDFC Bank').strip()
        simulated_outcome = request.form.get('simulated_outcome', 'success')  # 'success' or 'failure'
        
        if payment_mode == 'upi' or upi_id:
            upi_handle = upi_id or 'user@upi'
            payment_method = f"UPI ({upi_handle})"
            card_last4 = 'UPI'
        elif payment_mode == 'netbanking':
            payment_method = f"Net Banking ({bank_name})"
            card_last4 = 'NB'
        elif payment_mode == 'hub':
            payment_method = "Pay at Hub (Cash / UPI on Pickup)"
            card_last4 = 'HUB'
        else:
            if not payment_method:
                payment_method = 'Simulated RuPay / Card'
            card_last4 = card_number[-4:] if len(card_number) >= 4 else '6070'

        # Check vehicle availability again at point of payment to prevent double booking race conditions
        if not booking.vehicle.is_available_for_dates(booking.pickup_date, booking.return_date, exclude_booking_id=booking.id):
            flash('Another reservation was completed for this vehicle during your checkout. Please select alternate dates.', 'danger')
            booking.status = 'cancelled'
            booking.cancellation_reason = 'System cancellation: Vehicle reserved by overlapping booking before payment completion.'
            db.session.commit()
            return redirect(url_for('customer.vehicle_detail', vehicle_id=booking.vehicle_id))

        if simulated_outcome == 'success':
            # Create completed payment record
            payment = Payment(
                payment_reference=generate_payment_reference(),
                booking_id=booking.id,
                amount=booking.total_amount,
                payment_method=payment_method,
                transaction_id=generate_simulated_transaction_id(),
                card_last4=card_last4,
                cardholder_name=cardholder_name,
                status='completed',
                simulated_outcome='success'
            )
            db.session.add(payment)
            
            # Update booking status
            booking.status = 'confirmed'
            db.session.commit()

            flash('Simulated payment processed successfully! Your reservation is confirmed.', 'success')
            return redirect(url_for('customer.booking_confirmation', booking_ref=booking.booking_reference))
        else:
            # Create failed payment record
            failure_reason = request.form.get('failure_reason') or 'Simulated Card Decline: Insufficient funds or test card declined.'
            payment = Payment(
                payment_reference=generate_payment_reference(),
                booking_id=booking.id,
                amount=booking.total_amount,
                payment_method=payment_method,
                transaction_id=generate_simulated_transaction_id(),
                card_last4=card_last4,
                cardholder_name=cardholder_name,
                status='failed',
                simulated_outcome='failure',
                failure_reason=failure_reason
            )
            db.session.add(payment)
            # Booking remains pending_payment so user can retry or cancel
            db.session.commit()

            flash(f'Simulated payment failed: {failure_reason}. You can retry or choose another test scenario.', 'danger')
            return render_template('booking/checkout.html', booking=booking, last_payment=payment)

    last_payment = booking.latest_payment()
    return render_template('booking/checkout.html', booking=booking, last_payment=last_payment)


@customer_bp.route('/booking/confirmation/<booking_ref>')
@login_required
def booking_confirmation(booking_ref):
    booking = Booking.query.filter_by(booking_reference=booking_ref).first_or_404()
    user = get_current_user()

    if booking.user_id != user.id and not user.is_admin():
        abort(403)

    payment = booking.latest_payment()
    return render_template('booking/confirmation.html', booking=booking, payment=payment)


@customer_bp.route('/my-bookings')
@login_required
def booking_history():
    user = get_current_user()
    bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.created_at.desc()).all()
    return render_template('booking/history.html', bookings=bookings, today=date.today())


@customer_bp.route('/booking/<booking_ref>')
@login_required
def booking_detail(booking_ref):
    booking = Booking.query.filter_by(booking_reference=booking_ref).first_or_404()
    user = get_current_user()

    if booking.user_id != user.id and not user.is_admin():
        abort(403)

    payment = booking.latest_payment()
    can_cancel, cancel_msg = booking.can_be_cancelled()

    return render_template(
        'booking/detail.html',
        booking=booking,
        payment=payment,
        can_cancel=can_cancel,
        cancel_msg=cancel_msg,
        today=date.today()
    )


@customer_bp.route('/booking/<booking_ref>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_ref):
    booking = Booking.query.filter_by(booking_reference=booking_ref).first_or_404()
    user = get_current_user()

    if booking.user_id != user.id and not user.is_admin():
        abort(403)

    can_cancel, cancel_msg = booking.can_be_cancelled()
    if not can_cancel:
        flash(f'Cannot cancel reservation: {cancel_msg}', 'danger')
        return redirect(url_for('customer.booking_detail', booking_ref=booking.booking_reference))

    reason = request.form.get('cancellation_reason', 'Cancelled by customer').strip()

    booking.status = 'cancelled'
    booking.cancellation_reason = reason
    booking.cancelled_at = datetime.now(timezone.utc)

    # Refund payment if it was completed
    payment = booking.latest_payment()
    if payment and payment.status == 'completed':
        payment.status = 'refunded'

    db.session.commit()

    flash('Your booking has been cancelled and any simulated payment has been refunded.', 'info')
    return redirect(url_for('customer.booking_history'))
