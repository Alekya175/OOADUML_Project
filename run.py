import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    print(f"Starting Apex Drive Vehicle Rental System on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=debug)
