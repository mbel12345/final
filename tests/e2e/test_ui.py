import logging
import pytest
import re
import time

from fastapi.testclient import TestClient
from playwright.sync_api import expect

from app.main import app
from tests.conftest import BASE_PAGE
from tests.conftest import get_unique_user_data
from tests.conftest import goto
from tests.conftest import login
from tests.conftest import register_and_login

client = TestClient(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------
# Home Page
# ---------------------------------------------------

@pytest.mark.parametrize(
    'button_text, dest',
    [
        ('Login', '/login'),
        ('Register', '/register'),
        ('Create Free Account', '/register'),
        ('Sign In', '/login'),
    ],
)
def test_ui_home_links(page, fastapi_server, button_text, dest):

    # Test that links on the home page work

    goto(page, '/')
    link = page.locator(f'a:text("{button_text}")')
    expect(link).to_be_visible()
    link.click()
    page.wait_for_timeout(500)
    expect(page).to_have_url(f"{BASE_PAGE}/{dest.strip('/')}")

# ---------------------------------------------------
# Register
# ---------------------------------------------------

def test_ui_register(page, fastapi_server):

    # Test successful registration

    user = get_unique_user_data()

    goto(page, '/register')

    page.fill('#username', user['username'])
    page.fill('#email', user['email'])
    page.fill('#first_name', user['first_name'])
    page.fill('#last_name', user['last_name'])
    page.fill('#password', user['password'])
    page.fill('#confirm_password', user['password'])

    with page.expect_response('**/register') as response:
        page.click('button:text("Create Account")')

    assert response.value.status == 201

    page.wait_for_timeout(300)
    assert page.inner_text('#errorMessage') == ''
    assert page.inner_text('#successMessage') == 'Registration successful! Redirecting to login...'

    # Redirect back to login
    time.sleep(3)
    expect(page).to_have_url(f'{BASE_PAGE}/login')

def test_ui_register_short_password(page, fastapi_server):

    # Test that submit is rejected when password is too short

    user = get_unique_user_data()

    goto(page, '/register')

    page.fill('#username', user['username'])
    page.fill('#email', user['email'])
    page.fill('#first_name', user['first_name'])
    page.fill('#last_name', user['last_name'])
    page.fill('#password', 'Az0')
    page.fill('#confirm_password', 'Az0')

    page.click('button:text("Create Account")')

    page.wait_for_timeout(100)
    assert page.inner_text('#successMessage') == ''
    assert page.inner_text('#errorMessage') == 'Password must be at least 8 characters long and contain uppercase, lowercase, and numbers'

def test_ui_register_password_no_uppercase(page, fastapi_server):

    # Test that submit is rejected when password has no uppercase letters

    user = get_unique_user_data()

    goto(page, '/register')

    page.fill('#username', user['username'])
    page.fill('#email', user['email'])
    page.fill('#first_name', user['first_name'])
    page.fill('#last_name', user['last_name'])
    page.fill('#password', 'abcdefghi5')
    page.fill('#confirm_password', 'abcdefghi5')

    page.click('button:text("Create Account")')

    page.wait_for_timeout(100)
    assert page.inner_text('#successMessage') == ''
    assert page.inner_text('#errorMessage') == 'Password must be at least 8 characters long and contain uppercase, lowercase, and numbers'

def test_ui_register_password_no_lowercase(page, fastapi_server):

    # Test that submit is rejected when password has no lowercase letters

    user = get_unique_user_data()

    goto(page, '/register')

    page.fill('#username', user['username'])
    page.fill('#email', user['email'])
    page.fill('#first_name', user['first_name'])
    page.fill('#last_name', user['last_name'])
    page.fill('#password', 'ABCD12345')
    page.fill('#confirm_password', 'ABCD12345')

    page.click('button:text("Create Account")')

    page.wait_for_timeout(100)
    assert page.inner_text('#successMessage') == ''
    assert page.inner_text('#errorMessage') == 'Password must be at least 8 characters long and contain uppercase, lowercase, and numbers'

def test_ui_register_password_no_number(page, fastapi_server):

    # Test that submit is rejected when password has no number in it

    user = get_unique_user_data()

    goto(page, '/register')

    page.fill('#username', user['username'])
    page.fill('#email', user['email'])
    page.fill('#first_name', user['first_name'])
    page.fill('#last_name', user['last_name'])
    page.fill('#password', 'azABCDEFGH')
    page.fill('#confirm_password', 'azABCDEFGH')

    page.click('button:text("Create Account")')

    page.wait_for_timeout(100)
    assert page.inner_text('#successMessage') == ''
    assert page.inner_text('#errorMessage') == 'Password must be at least 8 characters long and contain uppercase, lowercase, and numbers'

def test_ui_register_password_mismatch(page, fastapi_server):

    # Test that submit is rejected when passwords do not match

    user = get_unique_user_data()

    goto(page, '/register')

    page.fill('#username', user['username'])
    page.fill('#email', user['email'])
    page.fill('#first_name', user['first_name'])
    page.fill('#last_name', user['last_name'])
    page.fill('#password', 'abc')
    page.fill('#confirm_password', 'xyz')

    page.click('button:text("Create Account")')

    page.wait_for_timeout(100)
    assert page.inner_text('#successMessage') == ''
    expect(page.locator('#passwordMatchError')).not_to_have_class(re.compile('hidden'))

# ---------------------------------------------------
# Login
# ---------------------------------------------------

def test_ui_login(page, fastapi_server):

    user = get_unique_user_data()

    # Register new user

    goto(page, '/register')

    page.fill('#username', user['username'])
    page.fill('#email', user['email'])
    page.fill('#first_name', user['first_name'])
    page.fill('#last_name', user['last_name'])
    page.fill('#password', user['password'])
    page.fill('#confirm_password', user['password'])

    with page.expect_response('**/register') as response:
        page.click('button:text("Create Account")')

    assert response.value.status == 201

    page.wait_for_timeout(500)
    assert page.inner_text('#errorMessage') == ''
    assert page.inner_text('#successMessage') == 'Registration successful! Redirecting to login...'

    # Redirect back to login

    time.sleep(3)
    expect(page).to_have_url(f'{BASE_PAGE}/login')

    # Do login

    page.fill('#username', user['username'])
    page.fill('#password', user['password'])

    with page.expect_response('**/login') as response:
        page.click('button:text("Sign in")')

    assert response.value.status == 200

    page.wait_for_timeout(300)
    assert page.inner_text('#errorMessage') == ''
    assert page.inner_text('#successMessage') == 'Login successful! Redirecting...'

    # Redirect to Dashboard

    time.sleep(3)
    expect(page).to_have_url(f'{BASE_PAGE}/dashboard')

def test_ui_login_wrong_password(page, fastapi_server):

    user = get_unique_user_data()

    # Register new user

    goto(page, '/register')

    page.fill('#username', user['username'])
    page.fill('#email', user['email'])
    page.fill('#first_name', user['first_name'])
    page.fill('#last_name', user['last_name'])
    page.fill('#password', user['password'])
    page.fill('#confirm_password', user['password'])

    with page.expect_response('**/register') as response:
        page.click('button:text("Create Account")')

    assert response.value.status == 201

    page.wait_for_timeout(300)
    assert page.inner_text('#errorMessage') == ''
    assert page.inner_text('#successMessage') == 'Registration successful! Redirecting to login...'

    # Redirect back to login

    time.sleep(3)
    expect(page).to_have_url(f'{BASE_PAGE}/login')

    # Do login with wrong password

    page.fill('#username', user['username'])
    page.fill('#password', user['password'] + 'wrong')

    with page.expect_response('**/login') as response:
        page.click('button:text("Sign in")')

    assert response.value.status == 401

    page.wait_for_timeout(500)
    assert page.inner_text('#successMessage') == ''
    assert page.inner_text('#errorMessage') == 'Invalid username or password'

# ---------------------------------------------------
# Dashboard
# ---------------------------------------------------

def test_ui_dashboard_create_calc(page, fastapi_server):

    # Test Dashboard calculation creation

    user_data = register_and_login(client)
    login(page, user_data)

    goto(page, '/dashboard')

    for op in ['Addition', 'Subtraction', 'Multiplication']:
        page.select_option('#calcType', op)
        page.fill('#calcInputs', '24, 10, 2.5')
        page.click('button:text("Calculate")')
        page.wait_for_timeout(100)

    page.wait_for_selector('text=24, 10, 2.5') # Wait for first row to load
    rows = page.locator('#calculationsTable tr')
    expect(rows).to_have_count(3)

    expect(rows.nth(0)).to_contain_text('addition')
    expect(rows.nth(0)).to_contain_text('24, 10, 2.5')
    expect(rows.nth(0)).to_contain_text('36.5')

    expect(rows.nth(1)).to_contain_text('subtraction')
    expect(rows.nth(1)).to_contain_text('24, 10, 2.5')
    expect(rows.nth(1)).to_contain_text('11.5')

    expect(rows.nth(2)).to_contain_text('multiplication')
    expect(rows.nth(2)).to_contain_text('24, 10, 2.5')
    expect(rows.nth(2)).to_contain_text('600')

def test_ui_dashboard_create_calc_invalid_inputs_success(page, fastapi_server):

    # Test Dashboard calculation creation with invalid inputs, where the calc still works

    user_data = register_and_login(client)
    login(page, user_data)

    goto(page, '/dashboard')

    for op in ['Addition', 'Subtraction', 'Multiplication']:
        page.select_option('#calcType', op)
        page.fill('#calcInputs', '24, 10, XXX, 2.5')
        page.click('button:text("Calculate")')
        page.wait_for_timeout(100)

    rows = page.locator('#calculationsTable tr')
    page.wait_for_selector("#calculationsTable tr:has-text('addition')")
    page.wait_for_selector("#calculationsTable tr:has-text('subtraction')")
    page.wait_for_selector("#calculationsTable tr:has-text('multiplication')")

    # Check rows

    rows = page.locator('#calculationsTable tr')
    addition_row = page.locator("#calculationsTable tr:has-text('addition')")
    subtraction_row = page.locator("#calculationsTable tr:has-text('subtraction')")
    multiplication_row = page.locator("#calculationsTable tr:has-text('multiplication')")

    expect(rows).to_have_count(3)

    expect(addition_row).to_contain_text('24, 10, 2.5')
    expect(addition_row).to_contain_text('36.5')

    expect(subtraction_row).to_contain_text('24, 10, 2.5')
    expect(subtraction_row).to_contain_text('11.5')

    expect(multiplication_row).to_contain_text('24, 10, 2.5')
    expect(multiplication_row).to_contain_text('600')

def test_ui_dashboard_create_calc_single_input_fail(page, fastapi_server):

    # Test Dashboard calculation creation with a single number, which should fail

    user_data = register_and_login(client)
    login(page, user_data)

    goto(page, '/dashboard')

    page.select_option('#calcType', 'Addition')
    page.fill('#calcInputs', '24')
    page.click('button:text("Calculate")')
    page.wait_for_timeout(100)

    error_message = page.locator('#errorMessage')
    expect(error_message).to_contain_text('Please enter at least two valid numbers, separated by commas')

def test_ui_dashboard_create_calc_invalid_inputs_fail(page, fastapi_server):

    # Test Dashboard calculation creation with a junk string that does contain nmbers, which should fail

    user_data = register_and_login(client)
    login(page, user_data)

    goto(page, '/dashboard')

    page.select_option('#calcType', 'Addition')
    page.fill('#calcInputs', '3, ,,,,; 4 : 5 ')
    page.click('button:text("Calculate")')
    page.wait_for_timeout(100)

    error_message = page.locator('#errorMessage')
    expect(error_message).to_contain_text('Please enter at least two valid numbers, separated by commas')

def test_ui_dashboard_create_calc_divide_by_zero(page, fastapi_server):

    # Test Dashboard calculation creation fails when division by zero is attempted

    user_data = register_and_login(client)
    login(page, user_data)

    goto(page, '/dashboard')

    page.select_option('#calcType', 'Division')
    page.fill('#calcInputs', '5, 0')
    page.click('button:text("Calculate")')
    page.wait_for_timeout(100)

    error_message = page.locator('#errorMessage')
    expect(error_message).to_contain_text('Cannot divide by zero')

def test_ui_dashboard_history(page, fastapi_server):

    # Test Dashboard calculation history table

    # Create calculations
    user_data = register_and_login(client)
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for op in ['addition', 'subtraction', 'multiplication']:
        payload = {
            'type': op,
            'inputs': [24, 10, 2.5],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    login(page, user_data)

    goto(page, '/dashboard')

   # Check rows

    rows = page.locator('#calculationsTable tr')
    addition_row = page.locator("#calculationsTable tr:has-text('addition')")
    subtraction_row = page.locator("#calculationsTable tr:has-text('subtraction')")
    multiplication_row = page.locator("#calculationsTable tr:has-text('multiplication')")

    expect(rows).to_have_count(3)

    expect(addition_row).to_contain_text('24, 10, 2.5')
    expect(addition_row).to_contain_text('36.5')

    expect(subtraction_row).to_contain_text('24, 10, 2.5')
    expect(subtraction_row).to_contain_text('11.5')

    expect(multiplication_row).to_contain_text('24, 10, 2.5')
    expect(multiplication_row).to_contain_text('600')

def test_ui_dashboard_delete(page, fastapi_server):

    # Test Dashboard delete calculation button

    # Create calculations
    user_data = register_and_login(client)
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for op in ['addition', 'subtraction', 'multiplication']:
        payload = {
            'type': op,
            'inputs': [24, 10, 2.5],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    # Verify history has 3 rows
    login(page, user_data)
    goto(page, '/dashboard')

    page.wait_for_selector('text=24, 10, 2.5') # Wait for first row to load
    rows = page.locator('#calculationsTable tr')
    expect(rows).to_have_count(3)

    # Click delete button for the first row
    delete_button = rows.nth(0).locator('button.delete-calc')

    assert delete_button.is_visible()
    page.once('dialog', lambda dialog: dialog.accept())
    delete_button.click()
    page.wait_for_timeout(1000)

    # Check that the row was deleted
    assert page.inner_text('#successMessage') == 'Calculation deleted successfully'

    # Check that the rows are as expected

    page.wait_for_selector('text=24, 10, 2.5') # Wait for first row to load
    rows = page.locator('#calculationsTable tr')
    expect(rows).to_have_count(2)

    expect(rows.nth(0)).to_contain_text('subtraction')
    expect(rows.nth(0)).to_contain_text('24, 10, 2.5')
    expect(rows.nth(0)).to_contain_text('11.5')

    expect(rows.nth(1)).to_contain_text('multiplication')
    expect(rows.nth(1)).to_contain_text('24, 10, 2.5')
    expect(rows.nth(1)).to_contain_text('600')

def test_ui_dashboard_logout(page, fastapi_server):

    # Test Logout button

    user_data = register_and_login(client)
    login(page, user_data)
    goto(page, '/dashboard')

    page.once('dialog', lambda dialog: dialog.accept())
    page.click('span:text("Logout")')

    expect(page).to_have_url(f'{BASE_PAGE}/login')

    # Test that access to dashboard is denied

    goto(page, '/dashboard')
    expect(page).to_have_url(f'{BASE_PAGE}/login')

def test_ui_dashboard_not_logged_in(page, fastapi_server):

    # Test that access to dashboard is denied

    goto(page, '/dashboard')

    expect(page).to_have_url(f'{BASE_PAGE}/login')

# ---------------------------------------------------
# View Calculation
# ---------------------------------------------------

def test_ui_view_calc(page, fastapi_server):

    # Create calculations
    user_data = register_and_login(client)
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for op in ['addition', 'subtraction', 'multiplication']:
        payload = {
            'type': op,
            'inputs': [24, 10, 2.5],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    login(page, user_data)

    goto(page, '/dashboard')

    # Go to view page for the first calc
    rows = page.locator('#calculationsTable tr')
    view_button = rows.nth(0).locator('a.view-calc')
    expect(view_button).to_be_visible()
    view_button.click()
    page.wait_for_timeout(1000)

    # Verify the view page

    calc_info = page.locator('#calcDetails .bg-blue-50')
    expect(calc_info).to_be_visible()
    expect(calc_info.locator('div').nth(0)).to_have_text('Result')
    expect(calc_info.locator('div').nth(1)).to_have_text('36.5')

    assert page.inner_text('#calc-inputs') == '24, 10, 2.5'

    preview = page.locator('#preview-div')
    expect(preview).to_be_visible()
    expect(preview.locator('div').nth(0)).to_have_text('24 +')
    expect(preview.locator('div').nth(1)).to_have_text('10 +')
    expect(preview.locator('div').nth(2)).to_have_text('2.5')
    expect(preview.locator('div').nth(4)).to_have_text('36.5')

def test_ui_view_calc_delete(page, fastapi_server):

    # Test delete button on View page

    # Create calculations
    user_data = register_and_login(client)
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for op in ['addition', 'subtraction', 'multiplication']:
        payload = {
            'type': op,
            'inputs': [24, 10, 2.5],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    login(page, user_data)

    goto(page, '/dashboard')

    # Go to view page for the first calc
    rows = page.locator('#calculationsTable tr')
    view_button = rows.nth(0).locator('a.view-calc')
    expect(view_button).to_be_visible()
    view_button.click()
    page.wait_for_timeout(1000)

    # Click delete button for the calc
    delete_button = page.locator('#deleteBtn')
    assert delete_button.is_visible()
    page.once('dialog', lambda dialog: dialog.accept())
    delete_button.click()
    page.wait_for_timeout(1000)

    # Check that the rows are as expected after re-routing to dashboard

    page.wait_for_selector('text=24, 10, 2.5') # Wait for first row to load
    rows = page.locator('#calculationsTable tr')
    expect(rows).to_have_count(2)

    expect(rows.nth(0)).to_contain_text('subtraction')
    expect(rows.nth(0)).to_contain_text('24, 10, 2.5')
    expect(rows.nth(0)).to_contain_text('11.5')

    expect(rows.nth(1)).to_contain_text('multiplication')
    expect(rows.nth(1)).to_contain_text('24, 10, 2.5')
    expect(rows.nth(1)).to_contain_text('600')

def test_ui_view_calc_logout(page, fastapi_server):

    # Test Logout button

    # Create calculations
    user_data = register_and_login(client)
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for op in ['addition', 'subtraction', 'multiplication']:
        payload = {
            'type': op,
            'inputs': [24, 10, 2.5],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    login(page, user_data)

    goto(page, '/dashboard')

    # Go to view page for the first calc
    rows = page.locator('#calculationsTable tr')
    view_button = rows.nth(0).locator('a.view-calc')
    expect(view_button).to_be_visible()
    view_button.click()
    page.wait_for_timeout(1000)

    # Logout
    page.once('dialog', lambda dialog: dialog.accept())
    page.click('span:text("Logout")')

    expect(page).to_have_url(f'{BASE_PAGE}/login')

def test_ui_view_calc_not_logged_in(page, fastapi_server):

    # Test that access to View page is denied

    # Create calculations
    user_data = register_and_login(client)
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for op in ['addition', 'subtraction', 'multiplication']:
        payload = {
            'type': op,
            'inputs': [24, 10, 2.5],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    login(page, user_data)

    goto(page, '/dashboard')

    # Go to view page for the first calc
    rows = page.locator('#calculationsTable tr')
    view_button = rows.nth(0).locator('a.view-calc')
    expect(view_button).to_be_visible()
    view_button.click()
    page.wait_for_timeout(1000)
    calc_id = page.url.split('/')[-1]

    # Logout
    page.once('dialog', lambda dialog: dialog.accept())
    page.click('span:text("Logout")')

    expect(page).to_have_url(f'{BASE_PAGE}/login')

    # Test that access to view page is denied

    goto(page, f'/dashboard/view/{calc_id}')
    expect(page).to_have_url(f'{BASE_PAGE}/login')

# ---------------------------------------------------
# Edit Calculation
# ---------------------------------------------------

def test_ui_edit_calc_pass(page, fastapi_server):

    # Test that calc can be edited

    # Create calculations
    user_data = register_and_login(client)
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for op in ['addition', 'subtraction', 'multiplication']:
        payload = {
            'type': op,
            'inputs': [24, 10, 2.5],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    login(page, user_data)

    goto(page, '/dashboard')

    # Go to edit page for the first calc
    rows = page.locator('#calculationsTable tr')
    edit_button = rows.nth(0).locator('a.edit-calc')
    expect(edit_button).to_be_visible()
    edit_button.click()
    page.wait_for_timeout(1000)

    # Fill inputs and click 'Save Changes'
    page.fill('#calcInputs', '34, 10, 6')
    update_button = page.locator('#submit-btn')
    assert update_button.is_visible()
    update_button.click()
    page.wait_for_timeout(1000)

    # Go to dashboard and wait for all rows to load
    goto(page, '/dashboard')
    page.wait_for_selector('text=34, 10, 6') # Wait for first row to load
    page.wait_for_selector("#calculationsTable tr:has-text('addition')")
    page.wait_for_selector("#calculationsTable tr:has-text('subtraction')")
    page.wait_for_selector("#calculationsTable tr:has-text('multiplication')")

    # Check rows

    rows = page.locator('#calculationsTable tr')
    addition_row = page.locator("#calculationsTable tr:has-text('addition')")
    subtraction_row = page.locator("#calculationsTable tr:has-text('subtraction')")
    multiplication_row = page.locator("#calculationsTable tr:has-text('multiplication')")

    expect(rows).to_have_count(3)

    expect(addition_row).to_contain_text('34, 10, 6')
    expect(addition_row).to_contain_text('50')

    expect(subtraction_row).to_contain_text('24, 10, 2.5')
    expect(subtraction_row).to_contain_text('11.5')

    expect(multiplication_row).to_contain_text('24, 10, 2.5')
    expect(multiplication_row).to_contain_text('600')

@pytest.mark.parametrize('invalid_input', [
    '',
    ' ',
    ',,,',
    'abc',
])
def test_ui_edit_calc_invalid_input(page, fastapi_server, invalid_input):

    # Test that error message is shown when invalid inputs are entered for calc edit

    # Create calculations
    user_data = register_and_login(client)
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for op in ['addition', 'subtraction', 'multiplication']:
        payload = {
            'type': op,
            'inputs': [24, 10, 2.5],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    login(page, user_data)

    goto(page, '/dashboard')

    # Go to edit page for the first calc
    rows = page.locator('#calculationsTable tr')
    edit_button = rows.nth(0).locator('a.edit-calc')
    expect(edit_button).to_be_visible()
    edit_button.click()
    page.wait_for_timeout(1000)

    # Fill inputs and click 'Save Changes'
    page.fill('#calcInputs', invalid_input)
    update_button = page.locator('#submit-btn')
    assert update_button.is_visible()
    update_button.click()
    page.wait_for_timeout(1000)

    assert page.inner_text('#successMessage') == ''
    assert page.inner_text('#errorMessage') == 'Please enter at least two valid numbers separated by commas.'

def test_ui_edit_calc_divide_by_zero(page, fastapi_server):

    # Test that error message is shown when the user attempts to divide by zero on Edit page

    # Create division calculation
    user_data = register_and_login(client)
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'type': 'division',
        'inputs': [5, 10],
        'user_id': 'ignore',
    }
    response = client.post('/calculations', json=payload, headers=headers)
    assert response.status_code == 201

    login(page, user_data)

    goto(page, '/dashboard')

    # Go to edit page for the division calc
    rows = page.locator('#calculationsTable tr')
    edit_button = rows.nth(0).locator('a.edit-calc')
    expect(edit_button).to_be_visible()
    edit_button.click()
    page.wait_for_timeout(1000)

    # Fill inputs and click 'Save Changes'
    page.fill('#calcInputs', '5, 0')
    update_button = page.locator('#submit-btn')
    assert update_button.is_visible()
    update_button.click()
    page.wait_for_timeout(1000)

    assert page.inner_text('#successMessage') == ''
    assert page.inner_text('#errorMessage') == 'Division by zero is not allowed.'
    assert page.inner_text('#previewResultValue') == 'Cannot divide by zero'

def test_ui_edit_calc_logout(page, fastapi_server):

    # Test Logout button on Edit Calc page

    # Create calculations
    user_data = register_and_login(client)
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for op in ['addition', 'subtraction', 'multiplication']:
        payload = {
            'type': op,
            'inputs': [24, 10, 2.5],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    login(page, user_data)

    goto(page, '/dashboard')

    # Go to edit page for the first calc
    rows = page.locator('#calculationsTable tr')
    edit_button = rows.nth(0).locator('a.edit-calc')
    expect(edit_button).to_be_visible()
    edit_button.click()
    page.wait_for_timeout(1000)

    # Logout
    page.once('dialog', lambda dialog: dialog.accept())
    page.click('span:text("Logout")')
    expect(page).to_have_url(f'{BASE_PAGE}/login')

def test_ui_edit_calc_not_logged_in(page, fastapi_server):

    # Test access is denied for Edit Calc page if not logged in

    # Create calculations
    user_data = register_and_login(client)
    access_token = user_data['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    for op in ['addition', 'subtraction', 'multiplication']:
        payload = {
            'type': op,
            'inputs': [24, 10, 2.5],
            'user_id': 'ignore',
        }
        response = client.post('/calculations', json=payload, headers=headers)
        assert response.status_code == 201

    login(page, user_data)

    goto(page, '/dashboard')

    # Go to edit page for the first calc
    rows = page.locator('#calculationsTable tr')
    edit_button = rows.nth(0).locator('a.edit-calc')
    expect(edit_button).to_be_visible()
    edit_button.click()
    page.wait_for_timeout(1000)
    calc_id = page.url.split('/')[-1]

    # Logout
    page.once('dialog', lambda dialog: dialog.accept())
    page.click('span:text("Logout")')
    expect(page).to_have_url(f'{BASE_PAGE}/login')

    # Test that access to view page is denied

    goto(page, f'/dashboard/edit/{calc_id}')
    expect(page).to_have_url(f'{BASE_PAGE}/login')
