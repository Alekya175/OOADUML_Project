from app.models import User

def test_user_registration(client, app):
    response = client.post('/auth/register', data={
        'full_name': 'Alice Wonder',
        'username': 'alicew',
        'email': 'alice@example.com',
        'phone': '1234567890',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username='alicew').first()
        assert user is not None
        assert user.email == 'alice@example.com'
        assert user.role == 'customer'
        assert user.check_password('Password123') is True
        assert user.check_password('WrongPass') is False

def test_registration_duplicate_username(client, sample_users):
    response = client.post('/auth/register', data={
        'full_name': 'Duplicate User',
        'username': 'testcustomer',  # Already taken
        'email': 'diff@example.com',
        'phone': '1234567890',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'already taken' in response.data.lower()

def test_registration_password_mismatch(client):
    response = client.post('/auth/register', data={
        'full_name': 'Mismatch Test',
        'username': 'mismatch',
        'email': 'mismatch@example.com',
        'phone': '1234567890',
        'password': 'Password123',
        'confirm_password': 'DifferentPass123'
    }, follow_redirects=True)

    assert b'do not match' in response.data.lower()

def test_login_success_and_logout(client, sample_users):
    # Customer Login
    response = client.post('/auth/login', data={
        'login_id': 'testcustomer',
        'password': 'CustomerPass123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Welcome back' in response.data

    # Logout
    logout_res = client.get('/auth/logout', follow_redirects=True)
    assert b'logged out' in logout_res.data.lower()

def test_login_invalid_credentials(client, sample_users):
    response = client.post('/auth/login', data={
        'login_id': 'testcustomer',
        'password': 'WrongPassword!'
    }, follow_redirects=True)

    assert b'Invalid username or password' in response.data

def test_admin_route_protection(client, sample_users):
    # Unauthenticated access
    res_unauth = client.get('/admin/dashboard', follow_redirects=True)
    assert b'Please log in' in res_unauth.data or b'Admin authentication required' in res_unauth.data

    # Customer user access blocked
    client.post('/auth/login', data={'login_id': 'testcustomer', 'password': 'CustomerPass123'})
    res_customer = client.get('/admin/dashboard', follow_redirects=True)
    assert b'Administrator privileges required' in res_customer.data

    # Admin access allowed
    client.get('/auth/logout')
    client.post('/auth/login', data={'login_id': 'testadmin', 'password': 'AdminPass123'})
    res_admin = client.get('/admin/dashboard')
    assert res_admin.status_code == 200
    assert b'Fleet Operations Dashboard' in res_admin.data
