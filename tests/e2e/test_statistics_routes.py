from fastapi.testclient import TestClient

from app.main import app
from app.models import CalcsPerDay
from app.models import Calculation
from tests.conftest import create_calcs_by_day
from tests.conftest import midnight_n_days_ago
from tests.conftest import register_and_login

client = TestClient(app)


# ---------------------------------------------------
# HTML Template
# ---------------------------------------------------


def test_statistics_page():

    # Test statistics page

    response = client.get('/statistics')
    assert response.status_code == 200
    assert 'Total Calculations' in response.text


# ---------------------------------------------------
# Total Calculations
# ---------------------------------------------------


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


# ---------------------------------------------------
# Calculations Per Day
# ---------------------------------------------------


def test_statistics_calcs_per_day_addition(db_session):

    # Test CalcsPerDay with addition

    # Create calculations
    user_data = register_and_login(client)
    create_calcs_by_day(user_data, db_session, client)

    # Get calculations
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get(
        '/statistics/calculations-per-day',
        headers=headers,
        params={
            'calc_type': 'addition',
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 8
    expected_counts = [6, 0, 0, 5, 4, 3, 2, 1]
    for i in range(len(data)):
        assert data[i]['calc_date'] + ' 00:00:00' == midnight_n_days_ago(len(data) - i - 1)
        assert data[i]['type'] == 'addition'
        assert data[i]['count'] == expected_counts[i]

    results = db_session.query(CalcsPerDay).where(CalcsPerDay.user_id == user_data['user_id']).all()
    assert(len(results)) == 8


def test_statistics_calcs_per_day_multiplication(db_session):

    # Test CalcsPerDay with multiplication

    # Create calculations
    user_data = register_and_login(client)
    create_calcs_by_day(user_data, db_session, client)

    # Get calculations
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get(
        '/statistics/calculations-per-day',
        headers=headers,
        params={
            'calc_type': 'multiplication',
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 15
    expected_counts = [20, 0, 0, 0, 0,
                       0, 0, 0, 0, 0,
                       0, 30, 0, 8, 7]
    for i in range(len(data)):
        assert data[i]['calc_date'] + ' 00:00:00' == midnight_n_days_ago(len(data) - i)
        assert data[i]['type'] == 'multiplication'
        assert data[i]['count'] == expected_counts[i]

    results = db_session.query(CalcsPerDay).where(CalcsPerDay.user_id == user_data['user_id']).all()
    assert(len(results)) == 15


def test_statistics_calcs_per_day_no_results(db_session):

    # Test CalcsPerDay with division (no results)

    # Create calculations
    user_data = register_and_login(client)
    create_calcs_by_day(user_data, db_session, client)

    # Get calculations
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get(
        '/statistics/calculations-per-day',
        headers=headers,
        params={
            'calc_type': 'division',
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

    results = db_session.query(CalcsPerDay).where(CalcsPerDay.user_id == user_data['user_id']).all()
    assert(len(results)) == 0


def test_statistics_calcs_per_day_all_calc_types(db_session):

    # Test CalcsPerDay for all calc types

    # Create calculations
    user_data = register_and_login(client)
    create_calcs_by_day(user_data, db_session, client)

    # Get calculations
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get(
        '/statistics/calculations-per-day',
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 16
    # x + y means total_addition_cals + total_multiplication_calcs
    expected_counts = [0 + 20, 0 +  0, 0 + 0, 0 + 0, 0 + 0,
                       0 +  0, 0 +  0, 0 + 0, 6 + 0, 0 + 0,
                       0 +  0, 5 + 30, 4 + 0, 3 + 8, 2 + 7,
                       1 + 0]
    for i in range(len(data)):
        assert data[i]['calc_date'] + ' 00:00:00' == midnight_n_days_ago(len(data) - i - 1)
        assert data[i]['type'] == None
        assert data[i]['count'] == expected_counts[i]

    results = db_session.query(CalcsPerDay).where(CalcsPerDay.user_id == user_data['user_id']).all()
    assert(len(results)) == 16


def test_statistics_calcs_per_day_start_filter(db_session):

    # Test CalcsPerDay with start_time filter

    # Create calculations
    user_data = register_and_login(client)
    create_calcs_by_day(user_data, db_session, client)

    # Get calculations
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get(
        '/statistics/calculations-per-day',
        headers=headers,
        params={
            'calc_type': 'addition',
            'start_time': midnight_n_days_ago(5),
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 6
    expected_counts = [0, 5, 4, 3, 2, 1]
    for i in range(len(data)):
        assert data[i]['calc_date'] + ' 00:00:00' == midnight_n_days_ago(len(data) - i - 1)
        assert data[i]['type'] == 'addition'
        assert data[i]['count'] == expected_counts[i]

    results = db_session.query(CalcsPerDay).where(CalcsPerDay.user_id == user_data['user_id']).all()
    assert(len(results)) == 6


def test_statistics_calcs_per_day_end_filter(db_session):

    # Test CalcsPerDay with end_time filter

    # Create calculations
    user_data = register_and_login(client)
    create_calcs_by_day(user_data, db_session, client)

    # Get calculations
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get(
        '/statistics/calculations-per-day',
        headers=headers,
        params={
            'calc_type': 'addition',
            'end_time': midnight_n_days_ago(3),
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 5
    expected_counts = [6, 0, 0, 5, 4]
    for i in range(len(data)):
        assert data[i]['calc_date'] + ' 00:00:00' == midnight_n_days_ago(len(data) - i + 2)
        assert data[i]['type'] == 'addition'
        assert data[i]['count'] == expected_counts[i]

    results = db_session.query(CalcsPerDay).where(CalcsPerDay.user_id == user_data['user_id']).all()
    assert(len(results)) == 5


def test_statistics_calcs_per_day_start_filter_and_end_filter(db_session):

    # Test CalcsPerDay with start_time filter and end_time filter

    # Create calculations
    user_data = register_and_login(client)
    create_calcs_by_day(user_data, db_session, client)

    # Get calculations
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get(
        '/statistics/calculations-per-day',
        headers=headers,
        params={
            'calc_type': 'addition',
            'start_time': midnight_n_days_ago(5),
            'end_time': midnight_n_days_ago(3),
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 3
    expected_counts = [0, 5, 4]
    for i in range(len(data)):
        assert data[i]['calc_date'] + ' 00:00:00' == midnight_n_days_ago(len(data) - i + 2)
        assert data[i]['type'] == 'addition'
        assert data[i]['count'] == expected_counts[i]

    results = db_session.query(CalcsPerDay).where(CalcsPerDay.user_id == user_data['user_id']).all()
    assert(len(results)) == 3


def test_statistics_calcs_per_day_cached(db_session):

    # Test CalcsPerDay with cached data in calcs_per_day table

    # Create calculations
    user_data = register_and_login(client)
    create_calcs_by_day(user_data, db_session, client)

    # Get calculations. Second iteration should trigger at least one cache hit.
    for i in range(2):
        access_token = user_data['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        response = client.get(
            '/statistics/calculations-per-day',
            headers=headers,
            params={
                'calc_type': 'multiplication',
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 15
        expected_counts = [20,  0, 0, 0, 0,
                            0,  0, 0, 0, 0,
                            0, 30, 0, 8, 7]
        for i in range(len(data)):
            assert data[i]['calc_date'] + ' 00:00:00' == midnight_n_days_ago(len(data) - i)
            assert data[i]['type'] == 'multiplication'
            assert data[i]['count'] == expected_counts[i]

        results = db_session.query(CalcsPerDay).where(CalcsPerDay.user_id == user_data['user_id']).all()
        assert(len(results)) == 15
