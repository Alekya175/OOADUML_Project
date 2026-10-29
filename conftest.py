import pytest
from datetime import date, timedelta
from decimal import Decimal
from app import create_app
from app.database import db
from app.models import User, Vehicle, Booking, Payment
from app.utils.booking_helpers import generate_booking_reference, generate_payment_reference, generate_simulated_transaction_id

class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'

@pytest.fixture
def app():
    test_app = create_app(TestConfig)
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def sample_users(app):
    admin = User(
        username='testadmin',
        email='admin@test.com',
        full_name='Test Admin',
        role='admin'
    )
    admin.set_password('AdminPass123')

    customer = User(
        username='testcustomer',
        email='customer@test.com',
        full_name='Test Customer',
        role='customer'
    )
    customer.set_password('CustomerPass123')

    db.session.add(admin)
    db.session.add(customer)
    db.session.commit()
    return {'admin': admin, 'customer': customer}

@pytest.fixture
def sample_vehicle(app):
    vehicle = Vehicle(
        name='Test Executive Sedan',
        make='Audi',
        model='A6',
        year=2024,
        vehicle_type='Sedan',
        location='Downtown Station',
        daily_rate=Decimal('100.00'),
        seating_capacity=5,
        transmission='Automatic',
        fuel_type='Petrol',
        status='available'
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle
