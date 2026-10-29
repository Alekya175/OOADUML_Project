from datetime import date, timedelta
from decimal import Decimal
from app.database import db
from app.models import Booking, Payment
from app.utils.booking_helpers import (
    generate_booking_reference, 
    generate_payment_reference, 
    generate_simulated_transaction_id
)

def test_booking_cancellation_rules_and_refund(client, app, sample_users, sample_vehicle):
    today = date.today()
    customer = sample_users['customer']
    vehicle = sample_vehicle

    # 1. Eligible future booking with completed payment
    future_booking = Booking(
        booking_reference=generate_booking_reference(),
        user_id=customer.id,
        vehicle_id=vehicle.id,
        pickup_date=today + timedelta(days=5),
        return_date=today + timedelta(days=8),
        total_days=3,
        daily_rate=vehicle.daily_rate,
        subtotal_amount=Decimal('300.00'),
        tax_amount=Decimal('24.00'),
        total_amount=Decimal('324.00'),
        status='confirmed'
    )
    db.session.add(future_booking)
    db.session.commit()

    payment = Payment(
        payment_reference=generate_payment_reference(),
        booking_id=future_booking.id,
        amount=future_booking.total_amount,
        payment_method='Simulated Visa Card',
        transaction_id=generate_simulated_transaction_id(),
        card_last4='1234',
        cardholder_name=customer.full_name,
        status='completed',
        simulated_outcome='success'
    )
    db.session.add(payment)
    db.session.commit()

    # Rule check: can be cancelled
    can_cancel, msg = future_booking.can_be_cancelled()
    assert can_cancel is True

    # Login as customer and perform cancellation
    client.post('/auth/login', data={'login_id': 'testcustomer', 'password': 'CustomerPass123'})
    res = client.post(f'/booking/{future_booking.booking_reference}/cancel', data={
        'cancellation_reason': 'Flight schedule shifted'
    }, follow_redirects=True)

    assert res.status_code == 200
    with app.app_context():
        updated_booking = db.session.get(Booking, future_booking.id)
        assert updated_booking.status == 'cancelled'
        assert updated_booking.cancellation_reason == 'Flight schedule shifted'
        assert updated_booking.cancelled_at is not None

        updated_payment = db.session.get(Payment, payment.id)
        assert updated_payment.status == 'refunded'

def test_cannot_cancel_past_booking(app, sample_users, sample_vehicle):
    today = date.today()
    customer = sample_users['customer']
    vehicle = sample_vehicle

    # Past booking
    past_booking = Booking(
        booking_reference=generate_booking_reference(),
        user_id=customer.id,
        vehicle_id=vehicle.id,
        pickup_date=today - timedelta(days=5),
        return_date=today - timedelta(days=2),
        total_days=3,
        daily_rate=vehicle.daily_rate,
        subtotal_amount=Decimal('300.00'),
        tax_amount=Decimal('24.00'),
        total_amount=Decimal('324.00'),
        status='completed'
    )
    db.session.add(past_booking)
    db.session.commit()

    can_cancel, msg = past_booking.can_be_cancelled()
    assert can_cancel is False
    assert 'cannot be cancelled' in msg.lower() or 'deadline passed' in msg.lower()
