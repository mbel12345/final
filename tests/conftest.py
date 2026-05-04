import logging
import pytest

from contextlib import contextmanager
from faker import Faker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import Generator

from app.database import get_engine
from app.database import get_sessionmaker
from app.database.database_init import drop_db
from app.database.database_init import init_db
from app.models.user import User

test_db = 'fastapi_db'
test_engine = get_engine(database_url=f'postgresql://postgres:postgres@localhost:5432/{test_db}')
TestingSessionLocal = get_sessionmaker(engine=test_engine)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

fake = Faker()
Faker.seed(12345)

def create_fake_user() -> dict[str, str]:

    # Generate a dictionary of fake user data for testing

    return {
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'email': fake.unique.email(),
        'username': fake.unique.user_name(),
        'password': fake.password(length=12),
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

@pytest.fixture(scope='session', autouse=True)
def setup_test_database():

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
def fake_user_data() -> dict[str, str]:

    # Provide fake user data
    return create_fake_user()

@pytest.fixture
def test_user(db_session: Session) -> User:

    # Create and return a single test user

    user_data = create_fake_user()
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
    users = [User(**create_fake_user()) for _ in range(num_users)]
    db_session.add_all(users)
    db_session.commit()
    logger.info(f'Seeded /{len(users)} users.')
    return users
