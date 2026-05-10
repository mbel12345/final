import logging
import pytest
import requests
import socket
import subprocess
import time

from contextlib import contextmanager
from datetime import datetime, timedelta
from playwright.sync_api import Browser, sync_playwright
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import Generator
from uuid import uuid4

from app.database import get_engine
from app.database import get_sessionmaker
from app.database.database_init import drop_db
from app.database.database_init import init_db
from app.models.calculation import Calculation
from app.models.user import User

test_db = 'fastapi_db'
test_engine = get_engine(database_url=f'postgresql://postgres:postgres@localhost:5432/{test_db}')
TestingSessionLocal = get_sessionmaker(engine=test_engine)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

BASE_PAGE = 'http://127.0.0.1:8002'


# ---------------------------------------------------
# Helper Functions
# ---------------------------------------------------


def get_unique_user_data():

    # Create user that has uuids in the email and password, to more reliably prevent variable conflicts

    unique_id = uuid4()
    return {
        'first_name': 'John',
        'last_name': 'Smith',
        'email': f'jsmith{unique_id}@example.com',
        'username': f'smith{unique_id}',
        'password': 'SecurePass123!',
    }


@contextmanager
def managed_db_session():

    # Context manager for safe database session handling
    session = TestingSessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f'Database error: {str(e)}')
        raise
    finally:
        session.close()


def goto(page, url):

    # Helper function to sanitize the URL and go to it

    final_url = f"{BASE_PAGE}/{url.lstrip('/')}"
    logger.info(f'goto: {final_url}')
    page.goto(final_url, wait_until='commit')


def login(page, user_info):

    # Login via UI, which needs to happen at beginning of each UI test

    goto(page, '/login')

    page.fill('#username', user_info['username'])
    page.fill('#password', user_info['password'])

    with page.expect_response('**/login') as response:
        page.click('button:text("Sign in")')

    assert response.value.status == 200

    time.sleep(3)


def midnight_n_days_ago(num_days: int):

    # Return YYYY-MM-DD 00:00:00 for the date num_days ago

    return (datetime.now() - timedelta(days=num_days)).replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')


def noon_n_days_ago(num_days: int):

    # Return YYYY-MM-DD 00:00:00 for the date num_days ago

    return (datetime.now() - timedelta(days=num_days)).replace(hour=12, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')


def create_calcs_by_day(user_data, db_session, client):

    # Create each calc on X days ago Y times

    token = user_data['access_token']
    user_id = user_data['user_id']
    headers = {'Authorization': f'Bearer {token}'}

    calc_freqs = [
        ('addition', 0, 1),
        ('addition', 1, 2),
        ('addition', 2, 3),
        ('addition', 3, 4),
        ('addition', 4, 5),
        ('addition', 7, 6),
        ('multiplication', 1, 7),
        ('multiplication', 2, 8),
        ('multiplication', 4, 30),
        ('multiplication', 15, 20),
   ]

    for op, days_ago, freq in calc_freqs:

       for i in range(freq):

            # Create calculation
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
            calculation.created_at = noon_n_days_ago(days_ago)
            db_session.commit()
            db_session.refresh(calculation)


# ---------------------------------------------------
# General Fixtures
# ---------------------------------------------------


@pytest.fixture(scope='session', autouse=True)
def setup_test_database(request):

    # Set up the test database before the session starts

    logger.info('Setting up test database...')

    try:
        drop_db(test_engine)
        init_db(test_engine)
        logger.info('Test database initialized')
    except Exception as e:
        logger.info(f'Error setting up test database: {str(e)}')

    yield

@pytest.fixture
def db_session() -> Generator[Session, None, None]:

    # Provide a test-scoped database session

    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@pytest.fixture
def test_user(db_session: Session) -> User:

    # Create and return a single test user

    user_data = get_unique_user_data()
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    logger.info(f'Created test user ID: {user.id}')
    return user

@pytest.fixture
def seed_users(db_session: Session, request) -> list[User]:

    # Seed mlutiple test users in the database

    num_users = getattr(request, 'param', 5)
    users = [User(**get_unique_user_data()) for _ in range(num_users)]
    db_session.add_all(users)
    db_session.commit()
    logger.info(f'Seeded /{len(users)} users.')
    return users

#########################################
# FastAPI fixtures
#########################################

def find_available_port() -> int:

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def wait_for_server(url: str, timeout: int = 30) -> bool:

    # Wait for the server to be ready

    start_time = time.time()
    while (time.time() - start_time) < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

class ServerStartupError(Exception):

    # Raised when the test server fails to start properly

    pass

@pytest.fixture(scope='session')
def fastapi_server():

    # Start a FastAPI test server

    base_port = 8002
    server_url = f'http://127.0.0.1:{base_port}/'

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('127.0.0.1', base_port)) == 0:
            base_port = find_available_port()
            server_url = f'http://127.0.0.1:{base_port}/'

    logger.info(f'Starting FastAPI server on port {base_port}...')

    process = subprocess.Popen(
        ['uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', str(base_port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd='.',
    )

    health_url = f'{server_url}health'
    if not wait_for_server(health_url, timeout=30):
        stderr = process.stderr.read()
        logger.error(f'Server failed ot start. Uvicorn error: {stderr}')
        process.terminate()
        raise ServerStartupError(f'Failed to start test server on {health_url}')

    logger.info(f'Test server running on {server_url}')
    yield server_url

    logger.info('Stopping test server...')
    process.terminate()
    try:
        process.wait(timeout=5)
        logger.info('Test server stopped.')
    except subprocess.TimeoutExpires:
        process.kill()
        logger.warning('Test server forcefully stopped.')

#########################################
# Playwright fixtures
#########################################

@pytest.fixture(scope='session')
def browser_context():

    # Provide a Playwright browser context for UI tests
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--allow-insecure-localhost',
                '--allow-running-insecure-content',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        logger.info('Playwright browser launched.')

        # Create a session-scoped context with routing rules
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
            bypass_csp=True,
        )

        # Disable external CSS/JS
        context.route("**/*", lambda route: (
            route.abort() if any(x in route.request.url for x in [
                'googleapis', 'gstatic', 'tailwind', 'unpkg'
            ]) else route.continue_()
        ))

        try:
            yield context
        finally:
            logger.info('Closing Playwright browser.')
            context.close()
            browser.close()

@pytest.fixture
def page(browser_context: Browser):

    # Provide a new browser page for each test. Closes the page and context after each test.

    page = browser_context.new_page()
    logger.info('New browser page created.')
    try:
        yield page
    finally:
        logger.info('Closing browser page.')
        page.close()

def register_and_login(client):

    # Helper function to register a new user and log in, returning the token response data

    user_data = get_unique_user_data()
    user_data['confirm_password'] = user_data['password']

    reg_response = client.post('/auth/register', json=user_data)
    assert reg_response.status_code == 201, f'User registration failed: {reg_response.text}'

    login_payload = {
        'username': user_data['username'],
        'password': user_data['password'],
    }
    login_response = client.post('/auth/login', json=login_payload)
    assert login_response.status_code == 200, f'Login failed: {login_response.text}'
    result = login_response.json()
    result['password'] = user_data['password']
    return result

def pytest_addoption(parser):

    '''
    Add custom command line options:
      --run-slow     : Run tests marked as 'slow'
    '''

    parser.addoption('--run-slow', action='store_true', help='Run tests marked as slow')

def pytest_collection_modifyitems(config, items):

    # Skip tests marked as 'slow' unless --run-slow is given

    if not config.getoption('--run-slow'):
        skip_slow = pytest.mark.skip(reason='use --run-slow to run')
        for item in items:
            if 'slow' in item.keywords:
                item.add_marker(skip_slow)
