import logging
import pytest

from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.user import User
from app.models.user import utcnow
from tests.conftest import create_fake_user
from tests.conftest import managed_db_session

logger = logging.getLogger(__name__)

def test_database_connection(db_session):

    # Verify the database connection is working

    result = db_session.execute(text('SELECT 1'))
    assert result.scalar() == 1
    logger.info('Database connection test passed')

def test_managed_session():

    # Test the managed_db_session context manager for one-off queries

    with managed_db_session() as session:

        session.execute(text('SELECT 1'))

        # Generate an error to trigger rollback
        with pytest.raises(ProgrammingError, match=''):
            session.execute(text('SELECT * FROM fake_table'))

def test_session_handling(db_session):

    '''
    Demonstrate partial commits:
      - user1 is committed successfully
      - user2 fails (duplicate email)
      - user3 is committed successfully
      - The final user count should be the initial count + 2
    '''

    initial_count = db_session.query(User).count()
    logger.info(f'Initial user count before test_session_handling: {initial_count}')

    # Create and commit user1
    user1 = User(
        first_name='User',
        last_name='One',
        email='user1@example.com',
        username='user1',
        password='hashed_password',
    )
    db_session.add(user1)
    db_session.commit()

    # Attempt to create user2 with a duplicate email
    user2 = User(
        first_name='User',
        last_name='Two',
        email='user1@example.com', # duplicate email
        username='user2',
        password='hashed_password',
    )
    db_session.add(user2)
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.info(f'Expected failure on duplicate user2: {e}')

    # Create and commit user3 with unique email/username
    user3 = User(
        first_name='User',
        last_name='Three',
        email='user3@example.com',
        username='user3',
        password='hashed_password',
    )
    db_session.add(user3)
    db_session.commit()

    # Verify 2 additional users have been added
    actual = db_session.query(User).count()
    expected = initial_count + 2
    assert actual == expected, f'Expected {expected} users after test, found {actual}'

def test_create_user_with_faker(db_session):

    # Create a single user using Faker-generated data

    user_data = create_fake_user()
    logger.info(f'Creating user with data: {user_data}')

    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == user_data['email']
    logger.info(f'Successfully created user with ID: {user.id}')

def test_create_multiple_users(db_session):

    # Create multiple users in a loop

    users = []
    for _ in range(3):
        user_data = create_fake_user()
        user = User(**user_data)
        users.append(user)
        db_session.add(user)

    db_session.commit()
    assert len(users) == 3
    logger.info(f'Successfully created {len(users)} users')

def test_query_methods(db_session, seed_users):

    # Demonstrate query methods using seeded users

    user_count = db_session.query(User).count()
    assert user_count >= len(seed_users), 'The user table should have at least the seeded users'

    first_user = seed_users[0]
    found = db_session.query(User).filter_by(
        email=first_user.email,
    ).first()
    assert found is not None, 'Should find the seeded user by email'

    users_by_email = db_session.query(User).order_by(User.email).all()
    assert len(users_by_email) >= len(seed_users), 'Query should return at least the seeded users'

def test_transaction_rollback(db_session):

    # Demonstrate how a partial transaction fails and triggers a rollback

    initial_count = db_session.query(User).count()

    try:
        user_data = create_fake_user()
        user = User(**user_data)
        db_session.add(user)
        db_session.execute(text('SELECT * FROM fake_table'))
        db_session.commit()
    except Exception:
        db_session.rollback()

    final_count = db_session.query(User).count()
    assert final_count == initial_count, 'The new user should not have been committed'

def test_update_with_refresh(db_session, test_user):

    # Update a user's email and refresh the session to see updated fields

    original_email = test_user.email
    original_update_time = test_user.updated_at

    new_email = f'new_{original_email}'
    test_user.email = new_email
    db_session.commit()
    db_session.refresh(test_user)

    assert test_user.email == new_email, 'Email should have been updated'
    assert test_user.updated_at > original_update_time, 'Updated time should be newer'
    logger.info(f'Successfully updated user {test_user.id}')

def test_bulk_operation(db_session):

    # Test bulk inserting mlutiple users at once

    user_data = [create_fake_user() for _ in range(10)]
    users = [User(**data) for data in user_data]
    db_session.bulk_save_objects(users)
    db_session.commit()

    count = db_session.query(User).count()
    assert count >= 10, 'At least 10 users should be in DB'
    logger.info(f'Successfully performed bulk operation with {len(users)} users')

def test_unique_email_constraint(db_session):

    # Create two users with the same email and expect an IntegrityError

    first_user_data = create_fake_user()
    first_user = User(**first_user_data)
    db_session.add(first_user)
    db_session.commit()

    second_user_data = create_fake_user()
    second_user_data['email'] = first_user_data['email']
    second_user = User(**second_user_data)
    db_session.add(second_user)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_user_persistence_after_constraint(db_session):

    '''
    - Create and commit a valid user
    - Attempt to create a duplicate user (same email) -> fails
    - Confirm the original user still exists
    '''

    initial_user_data = {
        'first_name': 'First',
        'last_name': 'User',
        'email': 'first@example.com',
        'username': 'firstuser',
        'password': 'password123',
    }
    initial_user = User(**initial_user_data)
    db_session.add(initial_user)
    db_session.add(initial_user)
    db_session.commit()
    db_session.refresh(initial_user)
    saved_id = initial_user.id

    try:
        duplicate_user = User(
            first_name='Second',
            last_name='User',
            email='first@example.com', # Duplicate
            username='seconduser',
            password='password456',
        )
        db_session.add(duplicate_user)
        db_session.commit()
        assert False, 'Should have raised IntegrityError'
    except IntegrityError:
        db_session.rollback()

    found_user = db_session.query(User).filter_by(
        id=saved_id,
    ).first()
    assert found_user is not None, 'Original user should exist'
    assert found_user.id == saved_id, 'Should find original user by ID'
    assert found_user.email == 'first@example.com', 'Email should be unchanged'
    assert found_user.username == 'firstuser', 'Username should be unchanged'

def test_error_handling():

    # Verify that a manual managed_db_session can capture and log invalid SQL errors

    with pytest.raises(Exception) as e:
        with managed_db_session() as session:
            session.execute(text('INVALID SQL'))
    assert 'INVALID SQL' in str(e.value)

def test_utcnow():

    # Test that utcnow() is accurate

    now = datetime.now(timezone.utc)
    utcnow_result = utcnow()
    assert now - utcnow_result < timedelta(seconds=1)

def test_init_with_hashed_password(db_session):

    # Test initializing a User with hashed_password included

    user_data = {
        'first_name': 'First',
        'last_name': 'User',
        'email': 'f_user@example.com',
        'username': 'f_user',
        'hashed_password': 'password123',
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    user_row = db_session.query(User).filter_by(
        email=user_data['email'],
    ).first()
    assert getattr(user_row, 'password') is not None

def test_user_repr():

    # Test that user.__repr__ works

    user_data = create_fake_user()
    user = User(**user_data)
    actual = str(user)
    expected = f"<User(name={user_data['first_name']} {user_data['last_name']}, email={user_data['email']})>"
    assert actual == expected

def test_user_update(db_session):

    # Test that user.update successfully updates User

    user_data = create_fake_user()
    user = User(**user_data)
    user.update(
        first_name='new_name',
    )
    db_session.add(user)
    db_session.commit()
    user_row = db_session.query(User).filter_by(
        email=user_data['email'],
    ).first()
    assert getattr(user_row, 'first_name') == 'new_name'

    now = datetime.now(timezone.utc)
    updated_at = getattr(user_row, 'updated_at')
    assert now - updated_at < timedelta(milliseconds=100)
