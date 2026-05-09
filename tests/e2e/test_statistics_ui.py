import logging
import pytest
import re

from fastapi.testclient import TestClient
from playwright.sync_api import expect

from app.main import app
from app.models import Calculation
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

    pie = page.locator('#calcsPie')
    expect(pie).not_to_have_class(re.compile('hidden'))
    data = page.evaluate(
    '''
    () => {
    const chart = Chart.getChart('calcsPie');
    return chart.data.datasets[0].data;
    }
    '''
    )
    assert data == expected


def fill_date_time_picker(page, _id, value):

    # Set the value of the date-picker, which is read-only and cannot be simply filled by page.fill()

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
    pie = page.locator('#calcsPie')
    expect(pie).to_have_class(re.compile('hidden'))
