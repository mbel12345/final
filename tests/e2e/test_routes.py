from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch
from uuid import uuid4

from app.main import app
from tests.conftest import register_and_login

client = TestClient(app)

# ---------------------------------------------------
# Helper Functions
# ---------------------------------------------------

def _parse_datetime(d: str) -> datetime:

    # Helper function to parse datetime strongs from API responses
    if d.endswith('Z'):
        d = d.replace('Z', '+00:00')
    return datetime.fromisoformat(d)

def create_calculation():

    # Helper function to create a new calculation

    token_data = register_and_login(client)
    access_token = token_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'type': 'addition',
        'inputs': [24, 8, 2.5],
        'user_id': 'ignore',
    }
    response = client.post('/calculations', json=payload, headers=headers)
    assert response.status_code == 201, f'Addition calculation creation failed: {response.text}'
    data = response.json()
    data['access_token'] = access_token
    expected = 34.5
    assert 'result' in data and data['result'] == expected, f"Expected result {expected}, got {data.get('result')}"
    return data

# ---------------------------------------------------
# Test FastAPI Lifespan
# ---------------------------------------------------

def test_lifespan():

    # Test lifespan function

    with patch('app.main.init_db') as mock_init:
        with TestClient(app) as client:
            # Trigger lifespan by making any request
            client.get("/health")

        mock_init.assert_called_once()

# ---------------------------------------------------
# Test Health Endpoint
# ---------------------------------------------------

def test_health_endpoint():

    # Test /health

    response = client.get('/health')
    assert response.status_code == 200, f'Expected status code 200 but got {response.status_code}. Response: {response.text}'
    assert response.json() == {'status': 'ok'}, 'Unexpected response from /health'

# ---------------------------------------------------
# Test Register and Login Endpoints
# ---------------------------------------------------

def test_user_registration():

    # Test user registration

    payload = {
        'first_name': 'Alice',
        'last_name': 'Smith',
        'email': 'alice.smith@example.com',
        'username': 'alicesmith',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!',
    }
    response = client.post('/auth/register', json=payload)
    assert response.status_code == 201, f'Expected 201 but got {response.status_code}. Response: {response.text}'
    data = response.json()
    for key in ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_verified']:
        assert key in data, f"Field '{key}' missing in response"
    assert data['username'] == payload['username']
    assert data['email'] == payload['email']
    assert data['first_name'] == payload['first_name']
    assert data['last_name'] == payload['last_name']
    assert data['is_active'] is True
    assert data['is_verified'] is False

def test_user_login():

    # Test valid login

    test_user = {
        'first_name': 'Bob',
        'last_name': 'Jones',
        'email': 'bob.jones@example.com',
        'username': 'bobjones',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!'
    }

    # Register user
    reg_response = client.post('/auth/register', json=test_user)
    assert reg_response.status_code == 201, f'User registration failed: {reg_response.text}'

    # Login user
    login_payload = {
        'username': test_user['username'],
        'password': test_user['password'],
    }
    login_response = client.post('/auth/login', json=login_payload)
    assert login_response.status_code == 200, f'Login failed: {login_response.text}'

    login_data = login_response.json()
    required_fields = {
        'access_token': str,
        'refresh_token': str,
        'token_type': str,
        'expires_at': str,
        'user_id': str,
        'username': str,
        'email': str,
        'first_name': str,
        'last_name': str,
        'is_active': bool,
        'is_verified': bool,
    }

    for field, expected_type in required_fields.items():
        assert field in login_data, f'Missing field: {field}'
        assert isinstance(login_data[field], expected_type), f'Field {field} has wrong type. Expected {expected_type}, got {type(login_data[field])}'

    assert login_data['token_type'].lower() == 'bearer', 'Token type should be bearer'
    assert len(login_data['access_token']) > 0, 'Access token should not be empty'
    assert len(login_data['refresh_token']) > 0, 'Refresh token should not be empty'
    assert login_data['username'] == test_user['username']
    assert login_data['email'] == test_user['email']
    assert login_data['first_name'] == test_user['first_name']
    assert login_data['last_name'] == test_user['last_name']
    assert login_data['is_active'] is True

    expires_at = _parse_datetime(login_data['expires_at'])
    current_time = datetime.now(timezone.utc)
    assert expires_at.tzinfo is not None, 'expires_at should be timezone-aware'
    assert current_time.tzinfo is not None, 'current_time should be timezone-aware'
    assert expires_at > current_time, 'Token expiration should be in the future'

def test_login_form():

    # Test correct password with login_form

    user_data = {
        'first_name': 'Calc',
        'last_name': 'Adder',
        'email': f'calc.adder{uuid4()}@example.com',
        'username': f'calc_adder_{uuid4()}',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!'
    }
    reg_response = client.post('/auth/register', json=user_data)
    assert reg_response.status_code == 201, f'User registration failed: {reg_response.text}'

    response = client.post('/auth/token', data={
        'username': user_data['username'],
        'password': user_data['password'],
    })
    assert response.status_code == 200
    assert 'access_token' in response.json()
    assert 'token_type' in response.json() and response.json()['token_type'] == 'bearer'

def test_user_registration_fail():

    # Test failure to register

    payload = {
        'first_name': 'Alice',
        'last_name': 'Smith',
        'email': 'alice.smith2@example.com',
        'username': 'alice1234',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!',
    }
    response = client.post('/auth/register', json=payload)
    assert response.status_code == 201, f'Expected 201 but got {response.status_code}. Response: {response.text}'

    # Duplicate registration
    response = client.post('/auth/register', json=payload)
    assert response.status_code == 400, f'Expected 400 but got {response.status_code}. Response: {response.text}'

def test_user_login_fail():

    # Test invalid login

    test_user = {
        'first_name': 'Bob',
        'last_name': 'Jones',
        'email': 'bob.jones2@example.com',
        'username': 'bobjones2',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!'
    }

    # Register user
    reg_response = client.post('/auth/register', json=test_user)
    assert reg_response.status_code == 201, f'User registration failed: {reg_response.text}'

    # Login user
    login_payload = {
        'username': test_user['username'],
        'password': test_user['password'] + 'xx',
    }
    login_response = client.post('/auth/login', json=login_payload)
    assert login_response.status_code == 401

def test_login_form_fail():

    # Test wrong password with login_form

    user_data = {
        'first_name': 'Calc',
        'last_name': 'Adder',
        'email': f'calc.adder{uuid4()}@example.com',
        'username': f'calc_adder_{uuid4()}',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!'
    }
    reg_response = client.post('/auth/register', json=user_data)
    assert reg_response.status_code == 201, f'User registration failed: {reg_response.text}'

    response = client.post('/auth/token', data={
        'username': user_data['username'],
        'password': user_data['password'] + 'xx',
    })
    assert response.status_code == 401

# ---------------------------------------------------
# Test HTML Templates
# ---------------------------------------------------

def test_home_page():

    # Test home page

    response = client.get('/')
    assert response.status_code == 200
    assert 'Welcome to the Calculations App' in response.text

def test_login_page():

    # Test login page

    response = client.get('/login')
    assert response.status_code == 200
    assert 'Welcome Back' in response.text

def test_register_page():

    # Test register page

    response = client.get('/register')
    assert response.status_code == 200
    assert 'Create Account' in response.text

def test_dashboard_page():

    # Test dashboard page

    response = client.get('/dashboard')
    assert response.status_code == 200
    assert 'Calculation History' in response.text

def test_view_calculation_page():

    # Test view calculation page

    calc_id = create_calculation()['id']
    response = client.get(f'/dashboard/view/{calc_id}')
    assert response.status_code == 200
    assert 'View Calculation' in response.text

def test_edit_calculation_page():

    # Test edit calculation page

    calc_id = create_calculation()['id']
    response = client.get(f'/dashboard/edit/{calc_id}')
    assert response.status_code == 200
    assert 'Edit Calculation' in response.text

# ---------------------------------------------------
# Calculation Tests
# ---------------------------------------------------

def test_create_calc_addition():

    # Test creation of Add calculation

    token_data = register_and_login(client)
    access_token = token_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'type': 'addition',
        'inputs': [24, 8, 2.5],
        'user_id': 'ignore',
    }
    response = client.post('/calculations', json=payload, headers=headers)
    assert response.status_code == 201, f'Addition calculation creation failed: {response.text}'
    data = response.json()
    expected = 34.5
    assert 'result' in data and data['result'] == expected, f"Expected result {expected}, got {data.get('result')}"

def test_create_calc_subtraction():

    # Test creation of Subtract calculation

    token_data = register_and_login(client)
    access_token = token_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'type': 'subtraction',
        'inputs': [24, 8, 2.5],
        'user_id': 'ignore',
    }
    response = client.post('/calculations', json=payload, headers=headers)
    assert response.status_code == 201, f'Subtraction calculation creation failed: {response.text}'
    data = response.json()
    expected = 13.5
    assert 'result' in data and data['result'] == expected, f"Expected result {expected}, got {data.get('result')}"

def test_create_calc_multiplication():

    # Test creation of Multiply calculation

    token_data = register_and_login(client)
    access_token = token_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'type': 'multiplication',
        'inputs': [24, 2, 1.5],
        'user_id': 'ignore',
    }
    response = client.post('/calculations', json=payload, headers=headers)
    assert response.status_code == 201, f'Multiplication calculation creation failed: {response.text}'
    data = response.json()
    expected = 72
    assert 'result' in data and data['result'] == expected, f"Expected result {expected}, got {data.get('result')}"

def test_create_calc_division():

    # Test creation of Add calculation

    token_data = register_and_login(client)
    access_token = token_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'type': 'division',
        'inputs': [24, 8, 2.5],
        'user_id': 'ignore',
    }
    response = client.post('/calculations', json=payload, headers=headers)
    assert response.status_code == 201, f'Division calculation creation failed: {response.text}'
    data = response.json()
    expected = 1.2
    assert 'result' in data and data['result'] == expected, f"Expected result {expected}, got {data.get('result')}"


def test_create_calc_divide_by_zero():

    # Attempt to add a calculation that does division by zero

    token_data = register_and_login(client)
    access_token = token_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'type': 'division',
        'inputs': [24, 8, 0],
        'user_id': 'ignore',
    }
    response = client.post('/calculations', json=payload, headers=headers)
    assert response.status_code == 422
    data = response.json()
    assert any('Cannot divide by zero' in e['msg'] for e in data['detail'])

def test_create_calc_invalid_type():

    # Attempt to add a calculation with an invalid type

    token_data = register_and_login(client)
    access_token = token_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'type': 'modulus',
        'inputs': [24, 8, 2.5],
        'user_id': 'ignore',
    }
    response = client.post('/calculations', json=payload, headers=headers)
    assert response.status_code == 422
    data = response.json()
    assert any('Type must be one of' in e['msg'] for e in data['detail'])


def test_create_calc_value_error(monkeypatch):

    # Force the "except ValueError" block to trigger for a calc

    def fake_create(*args, **kwargs):
        raise ValueError('Force failure')

    monkeypatch.setattr('app.main.Calculation.create', fake_create)

    token_data = register_and_login(client)
    access_token = token_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'type': 'addition',
        'inputs': [24, 8, 2.5],
        'user_id': 'ignore',
    }
    response = client.post('/calculations', json=payload, headers=headers)
    assert response.status_code == 400
    data = response.json()['detail'] == 'Force failure'

def test_list_calculations():

    # Test list of calculations for a user

    # Create calculations
    token_data = register_and_login(client)
    access_token = token_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for op in ['addition', 'subtraction', 'multiplication']:
        payload = {
            'type': op,
            'inputs': [24, 10, 2.5],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    # List calculations
    response = client.get('/calculations', headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    for i in range(3):
        assert data[i]['inputs'] == payload['inputs']
    assert data[0]['result'] == 36.5
    assert data[1]['result'] == 11.5
    assert data[2]['result'] == 600

def test_get_calculation():

    # Test successful fetch of a calculation

    calc = create_calculation()
    headers = {'Authorization': f"Bearer {calc['access_token']}"}

    response = client.get(f"/calculations/{calc['id']}", headers=headers)
    data = response.json()
    assert data['result'] == 34.5

def test_get_calculation_invalid_uuid():

    # Attempt to fetch an invalid calculation id format

    calc = create_calculation()
    headers = {'Authorization': f"Bearer {calc['access_token']}"}

    response = client.get(f'/calculations/100', headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data['detail'] == 'Invalid calculation id format'

def test_get_calculation_wrong_user():

    # Attempt to access another user's calculation

    calc = create_calculation()
    other_user = register_and_login(client)
    other_token = other_user['access_token']
    headers = {'Authorization': f"Bearer {other_token}"}

    response = client.get(f"/calculations/{calc['id']}", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data['detail'] == 'Calculation not found'

def test_update_calculation():

    # Test successful update of a calculation

    calc = create_calculation()
    headers = {'Authorization': f"Bearer {calc['access_token']}"}

    payload = {
        'inputs': [15, 20],
    }

    response = client.put(f"/calculations/{calc['id']}", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['inputs'] == payload['inputs']
    assert data['result'] == 35

    response = client.get(f"/calculations/{calc['id']}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['inputs'] == payload['inputs']
    assert data['result'] == 35

def test_update_calculation_invalid_uuid():

    # Attempt to update an invalid calculation id format

    calc = create_calculation()
    headers = {'Authorization': f"Bearer {calc['access_token']}"}

    payload = {
        'inputs': [15, 20],
    }

    response = client.put(f'/calculations/100', json=payload, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data['detail'] == 'Invalid calculation id format'

def test_update_calculation_wrong_user():

    # Attempt to update another user's calculation

    calc = create_calculation()
    other_user = register_and_login(client)
    other_token = other_user['access_token']
    headers = {'Authorization': f"Bearer {other_token}"}

    payload = {
        'inputs': [15, 20],
    }

    response = client.put(f"/calculations/{calc['id']}", json=payload, headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data['detail'] == 'Calculation not found'

def test_delete_calculation():

    # Test successful delete of a calculation

    calc = create_calculation()
    headers = {'Authorization': f"Bearer {calc['access_token']}"}

    response = client.delete(f"/calculations/{calc['id']}", headers=headers)
    assert response.status_code == 204
    assert response.content == b''

    response = client.get(f"/calculations/{calc['id']}", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data['detail'] == 'Calculation not found'

def test_delete_calculation_invalid_uuid():

    # Attempt to delete an invalid calculation id format

    calc = create_calculation()
    headers = {'Authorization': f"Bearer {calc['access_token']}"}

    response = client.delete(f'/calculations/100', headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data['detail'] == 'Invalid calculation id format'

def test_delete_calculation_wrong_user():

    # Attempt to delete another user's calculation

    calc = create_calculation()
    other_user = register_and_login(client)
    other_token = other_user['access_token']
    headers = {'Authorization': f"Bearer {other_token}"}

    response = client.delete(f"/calculations/{calc['id']}", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data['detail'] == 'Calculation not found'
