from flask import Blueprint, request, jsonify
from app.models import Vehicle
from app.utils.booking_helpers import parse_date, calculate_rental_quote

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/vehicles/<int:vehicle_id>/availability', methods=['GET'])
def check_availability(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'success': False, 'error': 'Vehicle not found'}), 404

    pickup_str = request.args.get('pickup_date', '').strip()
    return_str = request.args.get('return_date', '').strip()

    pickup_date = parse_date(pickup_str)
    return_date = parse_date(return_str)

    if not pickup_date or not return_date:
        return jsonify({
            'success': False,
            'error': 'Please provide valid pickup and return dates (YYYY-MM-DD).'
        }), 400

    quote = calculate_rental_quote(vehicle.daily_rate, pickup_date, return_date)
    if not quote['valid']:
        return jsonify({
            'success': False,
            'error': quote['error']
        }), 400

    is_available = vehicle.is_available_for_dates(pickup_date, return_date)

    return jsonify({
        'success': True,
        'available': is_available,
        'quote': quote,
        'message': 'Vehicle is available for your dates!' if is_available else 'Vehicle is already reserved for the selected dates.'
    })
