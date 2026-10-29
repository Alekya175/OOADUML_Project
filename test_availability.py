from datetime import date, timedelta
from decimal import Decimal
from app.database import db
from app.models import Booking
from app.utils.booking_helpers import generate_booking_reference

def test_overlapping_availability_conflicts(app, sample_users, sample_vehicle):
    today = date.today()
    customer = sample_users['customer']
    vehicle = sample_vehicle

    # Create an existing confirmed booking: Days +5 to +10
    b_start = today + timedelta(days=5)
    b_end = today + timedelta(days=10)

    confirmed_booking = Booking(
        booking_reference=generate_booking_reference(),
        user_id=customer.id,
        vehicle_id=vehicle.id,
        pickup_date=b_start,
        return_date=b_end,
        total_days=5,
        daily_rate=vehicle.daily_rate,
        subtotal_amount=Decimal('500.00'),
        tax_amount=Decimal('40.00'),
        total_amount=Decimal('540.00'),
        status='confirmed'
    )
    db.session.add(confirmed_booking)
    db.session.commit()

    # 1. Exact identical dates -> MUST CONFLICT
    assert vehicle.is_available_for_dates(b_start, b_end) is False

    # 2. Subset dates inside interval (Days +6 to +8) -> MUST CONFLICT
    assert vehicle.is_available_for_dates(today + timedelta(days=6), today + timedelta(days=8)) is False

    # 3. Overlapping start (Days +3 to +7) -> MUST CONFLICT
    assert vehicle.is_available_for_dates(today + timedelta(days=3), today + timedelta(days=7)) is False

    # 4. Overlapping end (Days +8 to +12) -> MUST CONFLICT
    assert vehicle.is_available_for_dates(today + timedelta(days=8), today + timedelta(days=12)) is False

    # 5. Enclosing interval (Days +4 to +11) -> MUST CONFLICT
    assert vehicle.is_available_for_dates(today + timedelta(days=4), today + timedelta(days=11)) is False

    # 6. Adjacent prior booking: ends exactly when confirmed booking starts (Days +2 to +5) -> ALLOWED
    assert vehicle.is_available_for_dates(today + timedelta(days=2), today + timedelta(days=5)) is True

    # 7. Adjacent next booking: starts exactly when confirmed booking ends (Days +10 to +14) -> ALLOWED
    assert vehicle.is_available_for_dates(today + timedelta(days=10), today + timedelta(days=14)) is True

    # 8. Cancelled booking should NOT block dates
    confirmed_booking.status = 'cancelled'
    db.session.commit()
    assert vehicle.is_available_for_dates(b_start, b_end) is True
