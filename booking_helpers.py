import uuid
from datetime import datetime, date, timezone
from decimal import Decimal, ROUND_HALF_UP

def parse_date(date_str: str) -> date:
    """Parse date from YYYY-MM-DD string, returning None if invalid."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
    except (ValueError, AttributeError):
        return None

def calculate_rental_quote(daily_rate, pickup_date: date, return_date: date, tax_rate: float = 0.08):
    """
    Calculate duration and total cost based on pickup and return dates.
    Validation rule:
    - return_date MUST be strictly after pickup_date.
    - Duration = (return_date - pickup_date).days
    - Rental days are counted as calendar 24-hour periods. For example, picking up on 
      Oct 1 and returning on Oct 3 counts as 2 rental days.
    """
    if not pickup_date or not return_date:
        return {
            'valid': False,
            'error': 'Please provide both valid pickup and return dates.'
        }

    today = date.today()
    if pickup_date < today:
        return {
            'valid': False,
            'error': 'Pickup date cannot be in the past.'
        }

    if return_date <= pickup_date:
        return {
            'valid': False,
            'error': 'Return date must be strictly after pickup date (minimum 1 day rental).'
        }

    days = (return_date - pickup_date).days
    rate = Decimal(str(daily_rate))
    subtotal = (rate * Decimal(days)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    tax = (subtotal * Decimal(str(tax_rate))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total = subtotal + tax

    return {
        'valid': True,
        'days': days,
        'daily_rate': float(rate),
        'subtotal': float(subtotal),
        'tax': float(tax),
        'total': float(total),
        'days_explanation': f'{days} day{"s" if days > 1 else ""} (from {pickup_date.strftime("%b %d, %Y")} to {return_date.strftime("%b %d, %Y")})'
    }

def generate_booking_reference() -> str:
    now_str = datetime.now(timezone.utc).strftime('%Y%m%d')
    suffix = uuid.uuid4().hex[:6].upper()
    return f"BK-{now_str}-{suffix}"

def generate_payment_reference() -> str:
    now_str = datetime.now(timezone.utc).strftime('%Y%m%d')
    suffix = uuid.uuid4().hex[:6].upper()
    return f"PAY-{now_str}-{suffix}"

def generate_simulated_transaction_id() -> str:
    suffix = uuid.uuid4().hex[:10].upper()
    return f"TXN-SIM-{suffix}"
