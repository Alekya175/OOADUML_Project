import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from app import create_app
from app.database import db
from app.models import User, Vehicle, Booking, Payment
from app.utils.booking_helpers import (
    generate_booking_reference, 
    generate_payment_reference, 
    generate_simulated_transaction_id
)

app = create_app()

INDIAN_VEHICLES = [
    # --- 2 WHEELERS ---
    {
        'name': 'Royal Enfield Classic 350 Reborn',
        'make': 'Royal Enfield',
        'model': 'Classic 350',
        'year': 2024,
        'category': '2 Wheeler',
        'vehicle_type': 'Cruiser',
        'location': 'Indiranagar Hub, Bengaluru',
        'daily_rate': Decimal('1200.00'),
        'seating_capacity': 2,
        'transmission': 'Manual',
        'fuel_type': 'Petrol',
        'mileage': '350 km/day',
        'image_url': '/static/images/cruiser_bike.jpg',
        'description': 'Iconic retro cruiser tuned for relaxed highway cruising and city thumping. Comes equipped with dual-channel ABS, comfortable touring split seats, and authentic timeless charm.',
        'features': '2x ISI Full-Face Helmets Included, Mobile Phone Mount with Fast USB Charger, Crash Guard, Dual Disc Brakes with ABS, Luggage Carrier',
        'status': 'available'
    },
    {
        'name': 'Honda Activa 6G DLX',
        'make': 'Honda',
        'model': 'Activa 6G',
        'year': 2024,
        'category': '2 Wheeler',
        'vehicle_type': 'Scooter',
        'location': 'BKC Hub, Mumbai',
        'daily_rate': Decimal('550.00'),
        'seating_capacity': 2,
        'transmission': 'Automatic',
        'fuel_type': 'Petrol',
        'mileage': 'Unlimited',
        'image_url': '/static/images/commuter_scooter.jpg',
        'description': "India's favorite city scooter with eSP technology, telescopic suspension, and hassle-free automatic CVT. The most convenient and economical choice for quick metro commutes.",
        'features': '1x ISI Standard Helmet, 18L Underseat Boot Storage, Combi Brake System (CBS), External Fuel Lid, USB Mobile Charger',
        'status': 'available'
    },
    {
        'name': 'KTM 390 Duke Gen-3',
        'make': 'KTM',
        'model': '390 Duke',
        'year': 2024,
        'category': '2 Wheeler',
        'vehicle_type': 'Sports Bike',
        'location': 'Cyber City Hub, Gurgaon (Delhi NCR)',
        'daily_rate': Decimal('1850.00'),
        'seating_capacity': 2,
        'transmission': 'Manual',
        'fuel_type': 'Petrol',
        'mileage': '300 km/day',
        'image_url': '/static/images/sports_bike.jpg',
        'description': 'The undisputed street-fighter king. Powered by a potent 399cc liquid-cooled engine with launch control, cornering traction control, Quickshifter+, and track-ready WP Apex suspension.',
        'features': '2x Premium ISI Helmets, Quickshifter+ Up/Down, 5-inch TFT Display with Smartphone Bluetooth GPS, Cornering MTC & Supermoto ABS, Type-C Fast Port',
        'status': 'available'
    },
    {
        'name': 'Ather 450X Gen-3 Apex',
        'make': 'Ather',
        'model': '450X Gen-3',
        'year': 2024,
        'category': '2 Wheeler',
        'vehicle_type': 'Electric Scooter',
        'location': 'Hitec City Hub, Hyderabad',
        'daily_rate': Decimal('750.00'),
        'seating_capacity': 2,
        'transmission': 'Automatic',
        'fuel_type': 'Electric',
        'mileage': '150 km/charge',
        'image_url': '/static/images/electric_scooter.jpg',
        'description': 'Smart high-performance electric scooter with lightning-quick Warp mode acceleration, Google Maps touchscreen dashboard, 110km real-world range, and access to the Ather Grid fast-charging network.',
        'features': '2x Helmets, 7-inch Water-resistant Touchscreen with Live Google Maps, AutoHold Hill Assist, Unlimited Ather Grid Charging Access, Reverse Mode',
        'status': 'available'
    },
    {
        'name': 'Royal Enfield Himalayan 450',
        'make': 'Royal Enfield',
        'model': 'Himalayan 450',
        'year': 2024,
        'category': '2 Wheeler',
        'vehicle_type': 'Adventure Bike',
        'location': 'Baga Beach Hub, North Goa',
        'daily_rate': Decimal('1650.00'),
        'seating_capacity': 2,
        'transmission': 'Manual',
        'fuel_type': 'Petrol',
        'mileage': '400 km/day',
        'image_url': '/static/images/adventure_bike.jpg',
        'description': 'Built for all roads and no roads. Powered by the high-revving Sherpa 450 liquid-cooled motor, 200mm long-travel suspension, Showa USD forks, and an integrated Tripper TFT navigation console.',
        'features': '2x Adventure Helmets, Full Map Navigation TFT Console, Switchable Rear ABS, Heavy-duty Engine Sump Guard, Touring Pannier Mounts',
        'status': 'available'
    },

    # --- 4 WHEELERS ---
    {
        'name': 'Mahindra Thar LX 4x4 Hard Top',
        'make': 'Mahindra',
        'model': 'Thar LX 4x4',
        'year': 2024,
        'category': '4 Wheeler',
        'vehicle_type': 'SUV',
        'location': 'Baga Beach Hub, North Goa',
        'daily_rate': Decimal('3800.00'),
        'seating_capacity': 4,
        'transmission': 'Automatic',
        'fuel_type': 'Diesel',
        'mileage': 'Unlimited',
        'image_url': '/static/images/adventure_truck.jpg',
        'description': 'Iconic authentic 4x4 off-roader with shift-on-the-fly four-wheel drive, mechanical locking rear differential, factory hard top, and supreme water-wading capability for thrilling coastal and mountain explorations.',
        'features': 'Mechanical 4WD with Low Range, 7-inch Touchscreen with Apple CarPlay/Android Auto, Pre-fitted Active FASTag, Roll Cage, Drizzle-resistant Cabin',
        'status': 'available'
    },
    {
        'name': 'Tata Nexon EV Long Range Empowered+',
        'make': 'Tata',
        'model': 'Nexon EV Long Range',
        'year': 2024,
        'category': '4 Wheeler',
        'vehicle_type': 'Electric',
        'location': 'Indiranagar Hub, Bengaluru',
        'daily_rate': Decimal('2400.00'),
        'seating_capacity': 5,
        'transmission': 'Automatic',
        'fuel_type': 'Electric',
        'mileage': '465 km ARAI Range',
        'image_url': '/static/images/electric_sedan.jpg',
        'description': "India's highest selling electric SUV with 465 km ARAI certified range, vehicle-to-vehicle charging capability, 360-degree surround cameras, ventilated leatherette seats, and silent effortless highway cruising.",
        'features': '12.3-inch Cinematic Touchscreen, JBL Cinematic Audio with Subwoofer, Pre-fitted Active FASTag, Paddle Shifters for Multi-mode Regen, Free Fast-charging at Tata Power EZ Hubs',
        'status': 'available'
    },
    {
        'name': 'Hyundai Creta SX(O) Turbo Knight',
        'make': 'Hyundai',
        'model': 'Creta SX(O)',
        'year': 2024,
        'category': '4 Wheeler',
        'vehicle_type': 'SUV',
        'location': 'Cyber City Hub, Gurgaon (Delhi NCR)',
        'daily_rate': Decimal('2800.00'),
        'seating_capacity': 5,
        'transmission': 'Automatic',
        'fuel_type': 'Petrol',
        'mileage': 'Unlimited',
        'image_url': '/static/images/modern_suv.jpg',
        'description': "The benchmark mid-size SUV in India. Loaded with Level 2 ADAS active safety suite, dual-pane panoramic sunroof, 8-speaker Bose audio, dual-zone climate control, and whisper-quiet ride comfort.",
        'features': 'Level 2 ADAS Safety Suite, Panoramic Sunroof, Bose Premium Sound System, Ventilated Front Seats, Pre-fitted Active FASTag, Wireless Phone Charging',
        'status': 'available'
    },
    {
        'name': 'Maruti Suzuki Swift ZXi Plus',
        'make': 'Maruti Suzuki',
        'model': 'Swift ZXi Plus',
        'year': 2024,
        'category': '4 Wheeler',
        'vehicle_type': 'Hatchback',
        'location': 'BKC Hub, Mumbai',
        'daily_rate': Decimal('1400.00'),
        'seating_capacity': 5,
        'transmission': 'Manual',
        'fuel_type': 'Petrol',
        'mileage': 'Unlimited',
        'image_url': '/static/images/urban_compact.jpg',
        'description': 'Nimble, fuel-efficient, and effortless to pilot through dense Indian city traffic. Boasts exceptional 25+ km/l fuel economy, 6 standard airbags, and a crisp 9-inch SmartPlay Pro+ touchscreen.',
        'features': '6 Standard Airbags, 25+ km/l Fuel Mileage, 9-inch SmartPlay Pro+ Touchscreen, Wireless Apple CarPlay/Android Auto, Pre-fitted Active FASTag, Rear Parking Camera',
        'status': 'available'
    },
    {
        'name': 'Toyota Fortuner Legender 4x4',
        'make': 'Toyota',
        'model': 'Fortuner Legender 4x4',
        'year': 2024,
        'category': '4 Wheeler',
        'vehicle_type': 'Luxury SUV',
        'location': 'Hitec City Hub, Hyderabad',
        'daily_rate': Decimal('6500.00'),
        'seating_capacity': 7,
        'transmission': 'Automatic',
        'fuel_type': 'Diesel',
        'mileage': 'Unlimited',
        'image_url': '/static/images/sports_coupe.jpg',
        'description': 'The undisputed ruler of Indian highways and rugged terrain. Legendary Toyota reliability backed by a muscular 204 PS 2.8L diesel engine, 500 Nm torque, 4x4 low range, and commanding road presence.',
        'features': '4x4 Heavy-Duty All-Terrain System, 7-Seater Premium Leather Seating, 11-Speaker JBL Audio System, Pre-fitted Active FASTag, Kick-Sensor Powered Tailgate',
        'status': 'available'
    },
    {
        'name': 'Mercedes-Benz E-Class E200 Exclusive',
        'make': 'Mercedes-Benz',
        'model': 'E-Class Exclusive',
        'year': 2024,
        'category': '4 Wheeler',
        'vehicle_type': 'Luxury',
        'location': 'Viman Nagar Hub, Pune Airport',
        'daily_rate': Decimal('12500.00'),
        'seating_capacity': 5,
        'transmission': 'Automatic',
        'fuel_type': 'Petrol',
        'mileage': '250 km/day',
        'image_url': '/static/images/luxury_sedan.jpg',
        'description': 'The pinnacle of luxury executive chauffeur travel in India. Features elongated rear legroom with 37-degree power reclining rear seats, Burmester 3D surround sound, and serene air suspension.',
        'features': 'Chauffeur Package with Reclining Rear Seats, Burmester 3D Surround Sound, Panoramic Sliding Sunroof, 64-Color Ambient Lighting, Pre-fitted Active FASTag, Wireless Rear Chauffeur Tablet',
        'status': 'available'
    }
]

def seed_database(force_reset=False):
    with app.app_context():
        # Ensure database tables exist
        db.create_all()

        if force_reset:
            print("Resetting database records for clean Indian fleet seeding...")
            Payment.query.delete()
            Booking.query.delete()
            Vehicle.query.delete()
            User.query.delete()
            db.session.commit()
        else:
            if User.query.filter_by(username='admin').first():
                print("Database already contains user records. Use force_reset=True to refresh.")
                return

        print("Seeding Indian demo users...")
        # 1. Admin User
        admin = User(
            username='admin',
            email='admin@apexdrive.in',
            full_name='Rajesh Sharma (Fleet Operations Head)',
            phone='+91 98201 12345',
            role='admin',
            is_active=True
        )
        admin.set_password('Admin@123')
        db.session.add(admin)

        # 2. Customer User
        customer = User(
            username='customer',
            email='priya.patel@example.in',
            full_name='Priya Patel',
            phone='+91 98450 67890',
            role='customer',
            is_active=True
        )
        customer.set_password('Customer@123')
        db.session.add(customer)

        db.session.commit()

        print(f"Seeding Indian fleet: {len(INDIAN_VEHICLES)} 2-wheelers and 4-wheelers...")
        vehicles = []
        for vdata in INDIAN_VEHICLES:
            v = Vehicle(**vdata)
            db.session.add(v)
            vehicles.append(v)

        db.session.commit()

        print("Seeding sample bookings and Indian simulated payments (UPI & RuPay)...")
        today = date.today()

        # 1. Past completed 2-wheeler booking (Royal Enfield Classic 350)
        v_2w = vehicles[0]
        pickup_past = today - timedelta(days=10)
        return_past = today - timedelta(days=7)
        days_past = 3
        rate_past = v_2w.daily_rate
        subtotal_past = rate_past * days_past
        tax_past = (subtotal_past * Decimal('0.08')).quantize(Decimal('0.01'))
        total_past = subtotal_past + tax_past

        b_past = Booking(
            booking_reference=generate_booking_reference(),
            user_id=customer.id,
            vehicle_id=v_2w.id,
            pickup_date=pickup_past,
            return_date=return_past,
            total_days=days_past,
            daily_rate=rate_past,
            subtotal_amount=subtotal_past,
            tax_amount=tax_past,
            total_amount=total_past,
            status='completed',
            notes='Weekend road trip to Nandi Hills. Helmets returned in excellent condition.'
        )
        db.session.add(b_past)
        db.session.flush()

        p_past = Payment(
            payment_reference=generate_payment_reference(),
            booking_id=b_past.id,
            amount=total_past,
            payment_method='UPI (Google Pay / PhonePe)',
            transaction_id='UPI-' + generate_simulated_transaction_id(),
            card_last4='UPI',
            cardholder_name=customer.full_name,
            status='completed',
            simulated_outcome='success'
        )
        db.session.add(p_past)

        # 2. Future confirmed 4-wheeler booking (Mahindra Thar 4x4)
        v_4w = vehicles[5]  # Thar
        pickup_future = today + timedelta(days=4)
        return_future = today + timedelta(days=8)
        days_future = 4
        rate_future = v_4w.daily_rate
        subtotal_future = rate_future * days_future
        tax_future = (subtotal_future * Decimal('0.08')).quantize(Decimal('0.01'))
        total_future = subtotal_future + tax_future

        b_future = Booking(
            booking_reference=generate_booking_reference(),
            user_id=customer.id,
            vehicle_id=v_4w.id,
            pickup_date=pickup_future,
            return_date=return_future,
            total_days=days_future,
            daily_rate=rate_future,
            subtotal_amount=subtotal_future,
            tax_amount=tax_future,
            total_amount=total_future,
            status='confirmed',
            notes='Goa coastal holiday. Requested pre-activated FASTag and hardtop variant.'
        )
        db.session.add(b_future)
        db.session.flush()

        p_future = Payment(
            payment_reference=generate_payment_reference(),
            booking_id=b_future.id,
            amount=total_future,
            payment_method='RuPay Platinum Debit Card',
            transaction_id='RUPAY-' + generate_simulated_transaction_id(),
            card_last4='6071',
            cardholder_name=customer.full_name,
            status='completed',
            simulated_outcome='success'
        )
        db.session.add(p_future)

        db.session.commit()
        print("Apex Drive India database initialized and Indian fleet successfully seeded!")

if __name__ == '__main__':
    force = '--reset' in sys.argv or '-r' in sys.argv
    seed_database(force_reset=force)
