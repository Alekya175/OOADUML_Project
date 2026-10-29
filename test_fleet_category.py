from decimal import Decimal
from datetime import date, timedelta
from app.models import Vehicle, Booking, Payment
from app.database import db

def test_vehicle_category_helpers(app):
    with app.app_context():
        bike = Vehicle(
            name='Royal Enfield Classic 350',
            make='Royal Enfield',
            model='Classic 350',
            year=2024,
            category='2 Wheeler',
            vehicle_type='Cruiser',
            location='Bengaluru Hub',
            daily_rate=Decimal('1200.00'),
            seating_capacity=2,
            transmission='Manual',
            fuel_type='Petrol',
            status='available'
        )
        car = Vehicle(
            name='Mahindra Thar 4x4',
            make='Mahindra',
            model='Thar',
            year=2024,
            category='4 Wheeler',
            vehicle_type='SUV',
            location='Goa Hub',
            daily_rate=Decimal('3800.00'),
            seating_capacity=4,
            transmission='Automatic',
            fuel_type='Diesel',
            status='available'
        )
        db.session.add(bike)
        db.session.add(car)
        db.session.commit()

        assert bike.is_two_wheeler is True
        assert bike.is_four_wheeler is False
        assert bike.category_icon == '🏍️'

        assert car.is_two_wheeler is False
        assert car.is_four_wheeler is True
        assert car.category_icon == '🚗'


def test_catalog_category_filtering(client, app):
    with app.app_context():
        bike = Vehicle(
            name='KTM 390 Duke',
            make='KTM',
            model='390 Duke',
            year=2024,
            category='2 Wheeler',
            vehicle_type='Sports Bike',
            location='Delhi Hub',
            daily_rate=Decimal('1850.00'),
            seating_capacity=2,
            transmission='Manual',
            fuel_type='Petrol',
            status='available'
        )
        car = Vehicle(
            name='Tata Nexon EV',
            make='Tata',
            model='Nexon EV',
            year=2024,
            category='4 Wheeler',
            vehicle_type='Electric',
            location='Bengaluru Hub',
            daily_rate=Decimal('2400.00'),
            seating_capacity=5,
            transmission='Automatic',
            fuel_type='Electric',
            status='available'
        )
        db.session.add(bike)
        db.session.add(car)
        db.session.commit()

    # 1. All vehicles
    res_all = client.get('/vehicles')
    assert res_all.status_code == 200
    assert b'KTM 390 Duke' in res_all.data
    assert b'Tata Nexon EV' in res_all.data

    # 2. Only 2-Wheelers
    res_2w = client.get('/vehicles?category=2+Wheeler')
    assert res_2w.status_code == 200
    assert b'KTM 390 Duke' in res_2w.data
    assert b'Tata Nexon EV' not in res_2w.data

    # 3. Only 4-Wheelers
    res_4w = client.get('/vehicles?category=4+Wheeler')
    assert res_4w.status_code == 200
    assert b'Tata Nexon EV' in res_4w.data
    assert b'KTM 390 Duke' not in res_4w.data


def test_admin_vehicle_category_filtering(client, app, sample_users):
    # Log in as admin
    client.post('/auth/login', data={'login_id': 'testadmin', 'password': 'AdminPass123'})

    with app.app_context():
        v1 = Vehicle(
            name='Ather 450X',
            make='Ather',
            model='450X',
            year=2024,
            category='2 Wheeler',
            vehicle_type='Electric Scooter',
            location='Hyderabad Hub',
            daily_rate=Decimal('750.00'),
            seating_capacity=2,
            transmission='Automatic',
            fuel_type='Electric',
            status='available'
        )
        v2 = Vehicle(
            name='Hyundai Creta',
            make='Hyundai',
            model='Creta',
            year=2024,
            category='4 Wheeler',
            vehicle_type='SUV',
            location='Mumbai Hub',
            daily_rate=Decimal('2800.00'),
            seating_capacity=5,
            transmission='Automatic',
            fuel_type='Petrol',
            status='available'
        )
        db.session.add(v1)
        db.session.add(v2)
        db.session.commit()

    res = client.get('/admin/vehicles?category=2+Wheeler')
    assert res.status_code == 200
    assert b'Ather 450X' in res.data
    assert b'Hyundai Creta' not in res.data


def test_upi_checkout_flow(client, app, sample_users):
    # Log in as customer
    client.post('/auth/login', data={'login_id': 'testcustomer', 'password': 'CustomerPass123'})

    with app.app_context():
        bike = Vehicle(
            name='Honda Activa 6G',
            make='Honda',
            model='Activa 6G',
            year=2024,
            category='2 Wheeler',
            vehicle_type='Scooter',
            location='Mumbai BKC Hub',
            daily_rate=Decimal('550.00'),
            seating_capacity=2,
            transmission='Automatic',
            fuel_type='Petrol',
            status='available'
        )
        db.session.add(bike)
        db.session.commit()
        bike_id = bike.id

    # Create pending reservation
    today = date.today()
    pickup = (today + timedelta(days=2)).isoformat()
    ret = (today + timedelta(days=5)).isoformat()

    reserve_res = client.post(f'/book/{bike_id}', data={
        'pickup_date': pickup,
        'return_date': ret,
        'notes': 'Daily city ride'
    }, follow_redirects=True)
    assert reserve_res.status_code == 200

    # Retrieve pending booking
    with app.app_context():
        booking = Booking.query.filter_by(vehicle_id=bike_id, status='pending_payment').first()
        assert booking is not None
        booking_ref = booking.booking_reference

    # Process UPI payment
    checkout_res = client.post(f'/checkout/{booking_ref}', data={
        'payment_mode': 'upi',
        'upi_id': 'customer@okaxis',
        'upi_name': 'Test Customer',
        'simulation_outcome': 'success'
    }, follow_redirects=True)

    assert checkout_res.status_code == 200

    with app.app_context():
        updated_booking = Booking.query.filter_by(booking_reference=booking_ref).first()
        assert updated_booking.status == 'confirmed'

        payment = Payment.query.filter_by(booking_id=updated_booking.id).first()
        assert payment is not None
        assert 'UPI' in payment.payment_method
        assert payment.card_last4 == 'UPI'
        assert payment.status == 'completed'
