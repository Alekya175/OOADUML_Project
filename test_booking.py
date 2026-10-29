from datetime import date, timedelta
from decimal import Decimal
from app.utils.booking_helpers import calculate_rental_quote

def test_booking_date_validation_rules():
    today = date.today()
    rate = Decimal('100.00')

    # 1. Past pickup date
    past_pickup = today - timedelta(days=2)
    past_return = today + timedelta(days=2)
    res_past = calculate_rental_quote(rate, past_pickup, past_return)
    assert res_past['valid'] is False
    assert 'past' in res_past['error'].lower()

    # 2. Return date same as pickup date (0 days)
    same_day = today + timedelta(days=5)
    res_same = calculate_rental_quote(rate, same_day, same_day)
    assert res_same['valid'] is False
    assert 'strictly after' in res_same['error'].lower()

    # 3. Return date before pickup date
    p_date = today + timedelta(days=5)
    r_date = today + timedelta(days=3)
    res_inverted = calculate_rental_quote(rate, p_date, r_date)
    assert res_inverted['valid'] is False
    assert 'strictly after' in res_inverted['error'].lower()

def test_booking_duration_and_pricing_calculation():
    today = date.today()
    rate = Decimal('150.00')

    # 1-day rental
    p1 = today + timedelta(days=1)
    r1 = today + timedelta(days=2)
    res1 = calculate_rental_quote(rate, p1, r1)
    assert res1['valid'] is True
    assert res1['days'] == 1
    assert res1['subtotal'] == 150.00
    assert res1['tax'] == 12.00  # 8% of 150
    assert res1['total'] == 162.00

    # 4-day rental
    p4 = today + timedelta(days=3)
    r4 = today + timedelta(days=7)
    res4 = calculate_rental_quote(rate, p4, r4)
    assert res4['valid'] is True
    assert res4['days'] == 4
    assert res4['subtotal'] == 600.00
    assert res4['tax'] == 48.00  # 8% of 600
    assert res4['total'] == 648.00
    assert '4 days' in res4['days_explanation']
