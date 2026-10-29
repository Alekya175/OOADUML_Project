from datetime import datetime, date, timezone
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import db

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(32), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='customer', index=True)  # 'customer' | 'admin'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_admin(self) -> bool:
        return self.role == 'admin'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    make = db.Column(db.String(64), nullable=False)
    model = db.Column(db.String(64), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(32), default='4 Wheeler', nullable=False, index=True)  # '2 Wheeler', '4 Wheeler'
    vehicle_type = db.Column(db.String(32), nullable=False, index=True)  # Sedan, SUV, Cruiser, Sports Bike, Scooter, etc.
    location = db.Column(db.String(120), nullable=False, index=True)      # Downtown HQ, Airport Terminal, Metro Center
    daily_rate = db.Column(db.Numeric(10, 2), nullable=False)
    seating_capacity = db.Column(db.Integer, default=5, nullable=False)
    transmission = db.Column(db.String(20), default='Automatic', nullable=False) # Automatic, Manual
    fuel_type = db.Column(db.String(32), default='Petrol', nullable=False)       # Petrol, Diesel, Electric, Hybrid
    mileage = db.Column(db.String(32), default='Unlimited', nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    features = db.Column(db.Text, nullable=True)  # Comma-separated or bullet list
    status = db.Column(db.String(20), default='available', nullable=False, index=True)  # available, maintenance, rented, inactive
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    bookings = db.relationship('Booking', backref='vehicle', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def features_list(self):
        if not self.features:
            return []
        return [f.strip() for f in self.features.split(',') if f.strip()]

    @property
    def is_two_wheeler(self):
        return self.category == '2 Wheeler'

    @property
    def is_four_wheeler(self):
        return self.category == '4 Wheeler'

    @property
    def category_icon(self):
        return '🏍️' if self.category == '2 Wheeler' else '🚗'

    def is_available_for_dates(self, pickup_date: date, return_date: date, exclude_booking_id: int = None) -> bool:
        """
        Check if vehicle is available for given date interval [pickup_date, return_date].
        Two intervals [p1, r1] and [p2, r2] overlap if p1 < r2 AND r1 > p2.
        Only 'confirmed' or 'pending_payment' bookings count as conflicting reservations.
        """
        if self.status != 'available':
            return False

        query = Booking.query.filter(
            Booking.vehicle_id == self.id,
            Booking.status.in_(['confirmed', 'pending_payment']),
            Booking.pickup_date < return_date,
            Booking.return_date > pickup_date
        )

        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        conflicts = query.count()
        return conflicts == 0

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'make': self.make,
            'model': self.model,
            'year': self.year,
            'category': self.category,
            'vehicle_type': self.vehicle_type,
            'location': self.location,
            'daily_rate': float(self.daily_rate) if self.daily_rate else 0.0,
            'seating_capacity': self.seating_capacity,
            'transmission': self.transmission,
            'fuel_type': self.fuel_type,
            'mileage': self.mileage,
            'image_url': self.image_url,
            'description': self.description,
            'features': self.features_list,
            'status': self.status
        }

    def __repr__(self):
        return f'<Vehicle {self.id}: {self.name} ({self.status})>'


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False, index=True)
    pickup_date = db.Column(db.Date, nullable=False, index=True)
    return_date = db.Column(db.Date, nullable=False, index=True)
    total_days = db.Column(db.Integer, nullable=False)
    daily_rate = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal_amount = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Status: pending_payment, confirmed, completed, cancelled
    status = db.Column(db.String(20), nullable=False, default='pending_payment', index=True)
    cancellation_reason = db.Column(db.Text, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    payments = db.relationship('Payment', backref='booking', lazy='dynamic', cascade='all, delete-orphan')

    def can_be_cancelled(self) -> tuple[bool, str]:
        """
        Cancellation Rule:
        A booking can be cancelled by customer if:
        1. Current status is 'pending_payment' or 'confirmed'
        2. Today's date is before the scheduled pickup date (or on pickup date before commencement)
        Returns (can_cancel: bool, reason_msg: str)
        """
        if self.status == 'cancelled':
            return False, "This booking has already been cancelled."
        if self.status == 'completed':
            return False, "Completed bookings cannot be cancelled."
        
        today = date.today()
        if today > self.pickup_date:
            return False, f"Cancellation deadline passed. Bookings can only be cancelled before pickup date ({self.pickup_date.strftime('%b %d, %Y')})."
        
        return True, "Eligible for free cancellation."

    def latest_payment(self):
        return self.payments.order_by(Payment.created_at.desc()).first()

    def to_dict(self):
        return {
            'id': self.id,
            'booking_reference': self.booking_reference,
            'user_id': self.user_id,
            'vehicle_id': self.vehicle_id,
            'pickup_date': self.pickup_date.isoformat(),
            'return_date': self.return_date.isoformat(),
            'total_days': self.total_days,
            'daily_rate': float(self.daily_rate),
            'subtotal_amount': float(self.subtotal_amount),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'status': self.status,
            'cancellation_reason': self.cancellation_reason,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Booking {self.booking_reference} ({self.status})>'


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    payment_reference = db.Column(db.String(32), unique=True, nullable=False, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(64), nullable=False) # 'Simulated Visa Card', 'Simulated Mastercard', etc.
    transaction_id = db.Column(db.String(64), unique=True, nullable=False)
    card_last4 = db.Column(db.String(4), nullable=True)
    cardholder_name = db.Column(db.String(120), nullable=True)
    
    # Status: pending, completed, failed, refunded
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    simulated_outcome = db.Column(db.String(20), nullable=False, default='success') # 'success' or 'failure'
    failure_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'payment_reference': self.payment_reference,
            'booking_id': self.booking_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'card_last4': self.card_last4,
            'cardholder_name': self.cardholder_name,
            'status': self.status,
            'simulated_outcome': self.simulated_outcome,
            'failure_reason': self.failure_reason,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Payment {self.payment_reference} - {self.status}>'
