from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.models import Calculation
from tests.conftest import register_and_login

client = TestClient(app)

# ---------------------------------------------------
# Helper Functions
# ---------------------------------------------------


def midnight_n_days_ago(num_days: int):

    # Return YYYY-MM-DD 00:00:00 for the date num_days ago

    return (datetime.now() - timedelta(days=num_days)).replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')


# ---------------------------------------------------
# Total Calculations
# ---------------------------------------------------


def test_statistics_page():

    # Test statistics page

    response = client.get('/statistics')
    assert response.status_code == 200
    assert 'Total Calculations' in response.text


def test_statistics_total_calcs():

    # Test listing of total calcs for each user

    # Create calculations
    token_data = register_and_login(client)
    access_token = token_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for op in ['addition', 'addition', 'subtraction', 'multiplication']:
        payload = {
            'type': op,
            'inputs': [24, 10, 2.5],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    response = client.get('/statistics/total-calculations', headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    data = {row['type']: row['count'] for row in data}
    assert data['addition'] == 2
    assert data['subtraction'] == 1
    assert data['multiplication'] == 1
    assert data['division'] == 0


def test_statistics_total_calcs_start_time_filter(db_session):

    # Test listing of total calcs for each user with start_time filter given

    # Create calculations
    token_data = register_and_login(client)
    access_token = token_data['access_token']
    user_id = token_data['user_id']
    headers = {'Authorization': f'Bearer {access_token}'}
    for i, op in enumerate(['addition', 'addition', 'subtraction', 'multiplication', 'addition', 'division']):

        # Create calculations
        payload = {
            'type': op,
            'inputs': [i, i],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

        # Simulate creating calculation at an older date
        if i >= 3:
            calculation = (
                db_session.query(Calculation)
                .filter(Calculation.user_id == user_id)
                .order_by(Calculation.created_at.desc())
                .first()
            )
            calculation.created_at = midnight_n_days_ago(3)
            db_session.commit()
            db_session.refresh(calculation)

    response = client.get(
        '/statistics/total-calculations',
        headers=headers,
        params={
            'start_time': midnight_n_days_ago(2),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    data = {row['type']: row['count'] for row in data}
    assert data['addition'] == 2
    assert data['subtraction'] == 1
    assert data['multiplication'] == 0
    assert data['division'] == 0


def test_statistics_total_calcs_end_time_filter(db_session):

    # Test listing of total calcs for each user with end_time filter given

    # Create calculations
    token_data = register_and_login(client)
    access_token = token_data['access_token']
    user_id = token_data['user_id']
    headers = {'Authorization': f'Bearer {access_token}'}
    for i, op in enumerate(['addition', 'addition', 'subtraction', 'multiplication', 'addition', 'division']):

        # Create calculations
        payload = {
            'type': op,
            'inputs': [i, i],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

        # Simulate creating calculation at an older date
        if i >= 3:
            calculation = (
                db_session.query(Calculation)
                .filter(Calculation.user_id == user_id)
                .order_by(Calculation.created_at.desc())
                .first()
            )
            calculation.created_at = midnight_n_days_ago(5)
            db_session.commit()
            db_session.refresh(calculation)

    response = client.get(
        '/statistics/total-calculations',
        headers=headers,
        params={
            'end_time': midnight_n_days_ago(2),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    data = {row['type']: row['count'] for row in data}
    assert data['addition'] == 1
    assert data['subtraction'] == 0
    assert data['multiplication'] == 1
    assert data['division'] == 1


def test_statistics_total_calcs_start_time_and_end_time_filter(db_session):

    # Test listing of total calcs for each user with start_time and end_time filters given

    # Create calculations
    token_data = register_and_login(client)
    access_token = token_data['access_token']
    user_id = token_data['user_id']
    headers = {'Authorization': f'Bearer {access_token}'}
    for i, op in enumerate(['addition', 'addition', 'subtraction', 'multiplication', 'addition', 'division']):

        # Create calculations
        payload = {
            'type': op,
            'inputs': [i, i],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

        # Simulate creating calculation at an older date
        calculation = (
            db_session.query(Calculation)
            .filter(Calculation.user_id == user_id)
            .order_by(Calculation.created_at.desc())
            .first()
        )
        calculation.created_at = midnight_n_days_ago(i)
        db_session.commit()
        db_session.refresh(calculation)

    response = client.get(
        '/statistics/total-calculations',
        headers=headers,
        params={
            'start_time': midnight_n_days_ago(4),
            'end_time': midnight_n_days_ago(2),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    data = {row['type']: row['count'] for row in data}
    assert data['addition'] == 1
    assert data['subtraction'] == 1
    assert data['multiplication'] == 1
    assert data['division'] == 0
