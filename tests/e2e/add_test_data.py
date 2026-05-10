'''
python3 -m tests.e2e.add_test_data
For testing line graph (calcs per day) feature.
This script creates a new user and inserts data into calcs_per_day table.
It prints the username + password, so that you can log in manually and view the line graph.
Important: You must use Start Time and End Time filters on the page, since there will be no data in calculations table for the user.
This data is necessary for dynamically determining start_time and end_time of the graph.
'''

import requests

from tests.conftest import get_unique_user_data

BASE_URL = 'http://localhost:8000'


def register_and_login():

    # Register

    reg_payload = get_unique_user_data()
    reg_payload['confirm_password'] = reg_payload['password']

    session = requests.Session()
    session.post(f'{BASE_URL}/auth/register', json=reg_payload)

    # Login
    login_payload = {
        'username': reg_payload['username'],
        'password': reg_payload['password'],
    }
    print(login_payload['username'])
    print(login_payload['password'])
    response = session.post(f'{BASE_URL}/auth/login', json=login_payload)
    response.raise_for_status()

    token = response.json()['access_token']
    user_id = response.json()['user_id']
    session.headers.update(
        {
            'Authorization': f'Bearer {token}',
        }
    )
    return session


def create_calcs_by_day(session):

    data = [
        {'calc_date': '2026-03-25', 'count': 40},
        {'calc_date': '2026-03-26', 'count': 30},
        {'calc_date': '2026-03-30', 'count': 80},
        {'calc_date': '2026-03-01', 'count': 45},
        {'calc_date': '2026-04-01', 'count': 100},
        {'calc_date': '2026-04-02', 'count': 5},
        {'calc_date': '2026-04-03', 'count': 40},
        {'calc_date': '2026-04-04', 'count': 68},
        {'calc_date': '2026-04-05', 'count': 30},
        {'calc_date': '2026-04-09', 'count': 90},
    ]

    for row in data:
        row['type'] = 'addition'

    response = session.post(f'{BASE_URL}/statistics/calculations-per-day', json=data)
    response.raise_for_status()


if __name__ == '__main__':

    session = register_and_login()
    create_calcs_by_day(session)
