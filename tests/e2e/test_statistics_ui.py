import logging
import pytest
import re

from fastapi.testclient import TestClient
from playwright.sync_api import expect

from app.main import app
from app.models import Calculation
from tests.conftest import create_calcs_by_day
from tests.conftest import goto
from tests.conftest import login
from tests.conftest import midnight_n_days_ago
from tests.conftest import register_and_login

client = TestClient(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------
# Helper Function
# ---------------------------------------------------


def create_calcs(user_data, db_session):

    # Create several calculations, each on different day (so that time filters can be tested)

    token = user_data['access_token']
    user_id = user_data['user_id']
    headers = {'Authorization': f'Bearer {token}'}

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


def check_total_calcs_chart(page, expected):

    # Verify pie chart for total calculations is present and has the correct data

    expect(page.locator('#errorMessage')).to_have_text('')
    expect(page.locator('#calcsPieContainer')).not_to_have_class(re.compile('hidden'))
    data = page.evaluate(
    '''
    () => {
    const chart = Chart.getChart('calcsPie');
    return chart.data.datasets[0].data;
    }
    '''
    )
    assert data == expected

def check_calcs_per_day_graph(page, expected):

    # Verify line graph for calculations per day is present and has the correct data

    expect(page.locator('#errorMessage')).to_have_text('')
    expect(page.locator('#lineGraphContainer')).not_to_have_class(re.compile('hidden'))
    data = page.evaluate(
    '''
    () => {
    const graph = Chart.getChart('lineGraph');
    return graph.data.datasets[0].data;
    }
    '''
    )
    assert data == expected


def fill_date_time_picker(page, _id, value):

    # Set the value of the date-picker, which is read-only and cannot be simply filled by page.fill()

    page.wait_for_selector(f'#{_id}')
    page.evaluate(
        """(value) => {
            const el = document.querySelector('#ELEMENT_ID');
            el.value = value;
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
        }""".replace('ELEMENT_ID', _id),
        value
    )


# ---------------------------------------------------
# Total Calculations
# ---------------------------------------------------


@pytest.mark.parametrize(
    'calc_type',
    [
        ('All'),
        ('Addition'),
    ],
)
def test_statistics_ui_total_calcs_basic(page, fastapi_server, db_session, calc_type):

    # On statistics page, test Total Calculations section

    user_data = register_and_login(client)
    login(page, user_data)
    create_calcs(user_data, db_session)

    goto(page, '/statistics')

    page.select_option('#calcType', calc_type)
    page.click('button:text("Filter")')
    page.wait_for_timeout(100)

    assert page.inner_text('#errorMessage') == ''
    assert page.inner_text('#additionCalcTotal') == '3'
    assert page.inner_text('#subtractionCalcTotal') == '1'
    assert page.inner_text('#multiplicationCalcTotal') == '1'
    assert page.inner_text('#divisionCalcTotal') == '1'
    check_total_calcs_chart(page, [3, 1, 1, 1])


@pytest.mark.parametrize(
    'calc_type',
    [
        ('All'),
        ('Addition'),
    ],
)
def test_statistics_ui_total_calcs_start_filter(page, fastapi_server, db_session, calc_type):

    # On statistics page, test Total Calculations section with start_time filter

    user_data = register_and_login(client)
    login(page, user_data)
    create_calcs(user_data, db_session)

    goto(page, '/statistics')

    page.select_option('#calcType', calc_type)
    fill_date_time_picker(page, 'startTime', midnight_n_days_ago(3))
    page.click('button:text("Filter")')
    page.wait_for_timeout(100)

    assert page.inner_text('#errorMessage') == ''
    assert page.inner_text('#additionCalcTotal') == '2'
    assert page.inner_text('#subtractionCalcTotal') == '1'
    assert page.inner_text('#multiplicationCalcTotal') == '1'
    assert page.inner_text('#divisionCalcTotal') == '0'
    check_total_calcs_chart(page, [2, 1, 1, 0])


@pytest.mark.parametrize(
    'calc_type',
    [
        ('All'),
        ('Addition'),
    ],
)
def test_statistics_ui_total_calcs_end_filter(page, fastapi_server, db_session, calc_type):

    # On statistics page, test Total Calculations section with end_time filter

    user_data = register_and_login(client)
    login(page, user_data)
    create_calcs(user_data, db_session)

    goto(page, '/statistics')

    page.select_option('#calcType', calc_type)
    fill_date_time_picker(page, 'endTime', midnight_n_days_ago(3))
    page.click('button:text("Filter")')
    page.wait_for_timeout(100)

    assert page.inner_text('#errorMessage') == ''
    assert page.inner_text('#additionCalcTotal') == '1'
    assert page.inner_text('#subtractionCalcTotal') == '0'
    assert page.inner_text('#multiplicationCalcTotal') == '1'
    assert page.inner_text('#divisionCalcTotal') == '1'
    check_total_calcs_chart(page, [1, 0, 1, 1])


@pytest.mark.parametrize(
    'calc_type',
    [
        ('All'),
        ('Addition'),
    ],
)
def test_statistics_ui_total_calcs_start_filter_and_end_filter(page, fastapi_server, db_session, calc_type):

    # On statistics page, test Total Calculations section with start_time filter and end_time filter

    user_data = register_and_login(client)
    login(page, user_data)
    create_calcs(user_data, db_session)

    goto(page, '/statistics')

    page.select_option('#calcType', calc_type)
    fill_date_time_picker(page, 'startTime', midnight_n_days_ago(3))
    fill_date_time_picker(page, 'endTime', midnight_n_days_ago(1))
    page.click('button:text("Filter")')
    page.wait_for_timeout(100)

    assert page.inner_text('#errorMessage') == ''
    assert page.inner_text('#additionCalcTotal') == '1'
    assert page.inner_text('#subtractionCalcTotal') == '1'
    assert page.inner_text('#multiplicationCalcTotal') == '1'
    assert page.inner_text('#divisionCalcTotal') == '0'
    check_total_calcs_chart(page, [1, 1, 1, 0])


@pytest.mark.parametrize(
    'calc_type',
    [
        ('All'),
        ('Addition'),
    ],
)
def test_statistics_ui_total_calcs_no_calcs(page, fastapi_server, calc_type):

    # On statistics page, test Total Calculations section when user has made no calcs

    user_data = register_and_login(client)
    login(page, user_data)

    goto(page, '/statistics')

    page.select_option('#calcType', calc_type)
    page.click('button:text("Filter")')
    page.wait_for_timeout(100)

    assert page.inner_text('#errorMessage') == ''
    assert page.inner_text('#additionCalcTotal') == '0'
    assert page.inner_text('#subtractionCalcTotal') == '0'
    assert page.inner_text('#multiplicationCalcTotal') == '0'
    assert page.inner_text('#divisionCalcTotal') == '0'
    expect(page.locator('#calcsPieContainer')).to_have_class(re.compile('hidden'))


# ---------------------------------------------------
# Calculations Per Day
# ---------------------------------------------------


def test_statistics_ui_calcs_per_day_addition(page, fastapi_server, db_session):

    # Test CalcsPerDay with addition

    # Create calculations
    user_data = register_and_login(client)
    login(page, user_data)
    create_calcs_by_day(user_data, db_session, client)

    goto(page, '/statistics')

    page.select_option('#calcType', 'Addition')
    with page.expect_response("**/statistics/calculations-per-day**") as response:
        page.click('button:text("Filter")')
    assert response.value.status == 200

    page.wait_for_timeout(100)

    check_calcs_per_day_graph(page, [6, 0, 0, 5, 4, 3, 2, 1])


def test_statistics_ui_calcs_per_day_multiplication(page, fastapi_server, db_session):

    # Test CalcsPerDay with multiplication

    # Create calculations
    user_data = register_and_login(client)
    login(page, user_data)
    create_calcs_by_day(user_data, db_session, client)

    goto(page, '/statistics')

    page.select_option('#calcType', 'Multiplication')
    with page.expect_response("**/statistics/calculations-per-day**") as response:
        page.click('button:text("Filter")')
    assert response.value.status == 200

    page.wait_for_timeout(100)

    check_calcs_per_day_graph(page, [
        20,  0, 0, 0, 0,
         0,  0, 0, 0, 0,
         0, 30, 0, 8, 7
    ])


def test_statistics_ui_calcs_per_day_no_results(page, fastapi_server, db_session):

    # Test CalcsPerDay with division (no results)

    # Create calculations
    user_data = register_and_login(client)
    login(page, user_data)
    create_calcs_by_day(user_data, db_session, client)

    goto(page, '/statistics')

    page.select_option('#calcType', 'Division')
    with page.expect_response("**/statistics/calculations-per-day**") as response:
        page.click('button:text("Filter")')
    assert response.value.status == 200

    expect(page.locator('#errorMessage')).to_have_text('')
    expect(page.locator('#lineGraphContainer')).to_have_class(re.compile('hidden'))


def test_statistics_ui_calcs_per_day_all_calc_types(page, fastapi_server, db_session):

    # Test CalcsPerDay for all calc types

    # Create calculations
    user_data = register_and_login(client)
    login(page, user_data)
    create_calcs_by_day(user_data, db_session, client)

    goto(page, '/statistics')

    page.select_option('#calcType', 'All')
    with page.expect_response("**/statistics/calculations-per-day**") as response:
        page.click('button:text("Filter")')
    assert response.value.status == 200

    page.wait_for_timeout(100)

    # x + y means total_addition_cals + total_multiplication_calcs
    expected = [
        0 + 20, 0 +  0, 0 + 0, 0 + 0, 0 + 0,
        0 +  0, 0 +  0, 0 + 0, 6 + 0, 0 + 0,
        0 +  0, 5 + 30, 4 + 0, 3 + 8, 2 + 7,
        1 + 0
    ]
    check_calcs_per_day_graph(page, expected)


def test_statistics_ui_calcs_per_day_start_filter(page, fastapi_server, db_session):

    # Test CalcsPerDay with start_time filter

    # Create calculations
    user_data = register_and_login(client)
    login(page, user_data)
    create_calcs_by_day(user_data, db_session, client)

    goto(page, '/statistics')

    page.select_option('#calcType', 'Addition')
    fill_date_time_picker(page, 'startTime', midnight_n_days_ago(5))
    with page.expect_response("**/statistics/calculations-per-day**") as response:
        page.click('button:text("Filter")')
    assert response.value.status == 200

    page.wait_for_timeout(100)

    check_calcs_per_day_graph(page, [0, 5, 4, 3, 2, 1])


def test_statistics_ui_calcs_per_day_end_filter(page, fastapi_server, db_session):

    # Test CalcsPerDay with end_time filter

    # Create calculations
    user_data = register_and_login(client)
    login(page, user_data)
    create_calcs_by_day(user_data, db_session, client)

    goto(page, '/statistics')

    page.select_option('#calcType', 'Addition')
    fill_date_time_picker(page, 'endTime', midnight_n_days_ago(3))
    with page.expect_response("**/statistics/calculations-per-day**") as response:
        page.click('button:text("Filter")')
    assert response.value.status == 200

    page.wait_for_timeout(100)

    check_calcs_per_day_graph(page, [6, 0, 0, 5, 4])


def test_statistics_ui_calcs_per_day_start_filter_and_end_filter(page, fastapi_server, db_session):

    # Test CalcsPerDay with start_time filter and end_time filter

    # Create calculations
    user_data = register_and_login(client)
    login(page, user_data)
    create_calcs_by_day(user_data, db_session, client)

    goto(page, '/statistics')

    page.select_option('#calcType', 'Addition')
    fill_date_time_picker(page, 'startTime', midnight_n_days_ago(5))
    fill_date_time_picker(page, 'endTime', midnight_n_days_ago(3))
    with page.expect_response("**/statistics/calculations-per-day**") as response:
        page.click('button:text("Filter")')
    assert response.value.status == 200

    page.wait_for_timeout(100)

    check_calcs_per_day_graph(page, [0, 5, 4])


# ---------------------------------------------------
# Average Operands
# ---------------------------------------------------


def test_statistics_ui_average_operands_basic(page, fastapi_server):

    # Test listing of average operands

    # Create calculations
    user_data = register_and_login(client)
    login(page, user_data)
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for i, op in enumerate(['addition', 'addition', 'subtraction', 'multiplication']):
        payload = {
            'type': op,
            'inputs': [4]*(i + 3),
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    # Go to stats page and click Filter
    goto(page, '/statistics')
    with page.expect_response("**/statistics/calculations-per-day**") as response:
        page.click('button:text("Filter")')
    assert response.value.status == 200

    # Check results
    expect(page.locator('#errorMessage')).to_have_text('')
    expect(page.locator('#additionAverageOperands')).to_have_text('3.5')
    expect(page.locator('#subtractionAverageOperands')).to_have_text('5')
    expect(page.locator('#multiplicationAverageOperands')).to_have_text('6')
    expect(page.locator('#divisionAverageOperands')).to_have_text('0')
    expect(page.locator('#allAverageOperands')).to_have_text('4.5')


def test_statistics_ui_average_operands_start_time_filter(page, fastapi_server, db_session):

    # Test average operands with start_time_filter

    # Create calculations
    user_data = register_and_login(client)
    login(page, user_data)
    access_token = user_data['access_token']
    user_id = user_data['user_id']
    headers = {'Authorization': f'Bearer {access_token}'}
    for i, op in enumerate(['addition', 'addition', 'subtraction', 'multiplication', 'addition', 'division']):

        # Create calculations
        payload = {
            'type': op,
            'inputs': [2]*(i + 2),
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

    # Go to stats page and click Filter
    goto(page, '/statistics')
    fill_date_time_picker(page, 'startTime', midnight_n_days_ago(2))
    with page.expect_response("**/statistics/calculations-per-day**") as response:
        page.click('button:text("Filter")')
    assert response.value.status == 200

    # Check results
    expect(page.locator('#errorMessage')).to_have_text('')
    expect(page.locator('#additionAverageOperands')).to_have_text('2.5')
    expect(page.locator('#subtractionAverageOperands')).to_have_text('4')
    expect(page.locator('#multiplicationAverageOperands')).to_have_text('0')
    expect(page.locator('#divisionAverageOperands')).to_have_text('0')
    expect(page.locator('#allAverageOperands')).to_have_text('3')


def test_statistics_ui_average_operands_end_time_filter(page, fastapi_server, db_session):

    # Test average operands with end_time_filter

    # Create calculations
    user_data = register_and_login(client)
    login(page, user_data)
    access_token = user_data['access_token']
    user_id = user_data['user_id']
    headers = {'Authorization': f'Bearer {access_token}'}
    for i, op in enumerate(['addition', 'addition', 'subtraction', 'multiplication', 'addition', 'division']):

        # Create calculations
        payload = {
            'type': op,
            'inputs': [2]*(i + 2),
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

    # Go to stats page and click Filter
    goto(page, '/statistics')
    fill_date_time_picker(page, 'endTime', midnight_n_days_ago(2))
    with page.expect_response("**/statistics/calculations-per-day**") as response:
        page.click('button:text("Filter")')
    assert response.value.status == 200

    # Check results
    expect(page.locator('#errorMessage')).to_have_text('')
    expect(page.locator('#additionAverageOperands')).to_have_text('6')
    expect(page.locator('#subtractionAverageOperands')).to_have_text('0')
    expect(page.locator('#multiplicationAverageOperands')).to_have_text('5')
    expect(page.locator('#divisionAverageOperands')).to_have_text('7')
    expect(page.locator('#allAverageOperands')).to_have_text('6')


def test_statistics_ui_average_operands_start_time_and_end_time_filter(page, fastapi_server, db_session):

    # Test average_operands with start_time_filter and end_time_filter

    # Create calculations
    user_data = register_and_login(client)
    login(page, user_data)
    access_token = user_data['access_token']
    user_id = user_data['user_id']
    headers = {'Authorization': f'Bearer {access_token}'}
    for i, op in enumerate(['addition', 'addition', 'subtraction', 'multiplication', 'addition', 'division']):

        # Create calculations
        payload = {
            'type': op,
            'inputs': [2]*(i + 2),
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

    # Go to stats page and click Filter
    goto(page, '/statistics')
    fill_date_time_picker(page, 'startTime', midnight_n_days_ago(4))
    fill_date_time_picker(page, 'endTime', midnight_n_days_ago(2))
    with page.expect_response("**/statistics/calculations-per-day**") as response:
        page.click('button:text("Filter")')
    assert response.value.status == 200

    # Check results
    expect(page.locator('#errorMessage')).to_have_text('')
    expect(page.locator('#additionAverageOperands')).to_have_text('6')
    expect(page.locator('#subtractionAverageOperands')).to_have_text('4')
    expect(page.locator('#multiplicationAverageOperands')).to_have_text('5')
    expect(page.locator('#divisionAverageOperands')).to_have_text('0')
    expect(page.locator('#allAverageOperands')).to_have_text('5')


def test_statistics_ui_average_operands_no_calcs(page, fastapi_server, db_session):

    # Test average_operands when user has made no calcs

    # Login
    user_data = register_and_login(client)
    login(page, user_data)

    # Go to stats page and click Filter
    goto(page, '/statistics')
    with page.expect_response("**/statistics/calculations-per-day**") as response:
        page.click('button:text("Filter")')
    assert response.value.status == 200

    # Check results
    expect(page.locator('#errorMessage')).to_have_text('')
    expect(page.locator('#additionAverageOperands')).to_have_text('0')
    expect(page.locator('#subtractionAverageOperands')).to_have_text('0')
    expect(page.locator('#multiplicationAverageOperands')).to_have_text('0')
    expect(page.locator('#divisionAverageOperands')).to_have_text('0')
    expect(page.locator('#allAverageOperands')).to_have_text('0')
