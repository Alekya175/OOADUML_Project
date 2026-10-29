import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def ensure_database():
    host = os.getenv('MYSQL_HOST', '127.0.0.1')
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', 'root')
    port = int(os.getenv('MYSQL_PORT', '3306'))
    db_name = os.getenv('MYSQL_DB', 'vehicle_rental_db')

    print(f"Connecting to MySQL at {host}:{port} as user '{user}'...")
    try:
        conn = pymysql.connect(host=host, user=user, password=password, port=port)
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            print(f"Database '{db_name}' ensured.")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Notice during MySQL check: {e}")

if __name__ == '__main__':
    ensure_database()
    from seed_data import seed_database
    seed_database()
