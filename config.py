import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-vehicle-rental-2026-xyz!')
    
    # Database Configuration
    # Supports MySQL or fallback SQLite
    DB_USER = os.getenv('MYSQL_USER', 'root')
    DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')
    DB_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    DB_PORT = os.getenv('MYSQL_PORT', '3306')
    DB_NAME = os.getenv('MYSQL_DB', 'vehicle_rental_db')
    
    # Default connection string for MySQL
    DEFAULT_MYSQL_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', DEFAULT_MYSQL_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True
    }
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # App Settings
    CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '₹')
    TAX_RATE = 0.08  # 8% tax & service fees
    
    # Cancellation rule: Cancellation allowed strictly prior to pickup date (>= 0 days before start)
    CANCELLATION_POLICY_DESC = "Free cancellation is permitted at any time prior to the scheduled pickup date. Full simulated refund will be issued."
