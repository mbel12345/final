import pytest

from datetime import datetime, timezone
from fastapi import HTTPException, status
from unittest.mock import patch
from uuid import uuid4

from app.auth.dependencies import get_current_active_user, get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

sample_user_data = {
     'id': uuid4(),
    'username': 'testuser',
    'email': 'test@example.com',
    'first_name': 'Test',
    'last_name': 'User',
    'is_active': True,
    'is_verified': True,
    'created_at': datetime.now(timezone.utc),
    'updated_at': datetime.now(timezone.utc),
}

inactive_user_data = {
    'id': uuid4(),
    'username': 'inactiveuser',
    'email': 'inactive@example.com',
    'first_name': 'Inactive',
    'last_name': 'User',
    'is_active': False,
    'is_verified': False,
    'created_at': datetime.now(timezone.utc),
    'updated_at': datetime.now(timezone.utc),
}

@pytest.fixture
def mock_verify_token():

    with patch.object(User, 'verify_token') as mock:
        yield mock

def test_get_current_user_valid_token_existing_user(mock_verify_token):

    # Test get_current_user with valid token and complete payload

    mock_verify_token.return_value = sample_user_data

    user_response = get_current_user(token='validtoken')

    assert isinstance(user_response, UserResponse)
    assert user_response.id == sample_user_data["id"]
    assert user_response.username == sample_user_data["username"]
    assert user_response.email == sample_user_data["email"]
    assert user_response.first_name == sample_user_data["first_name"]
    assert user_response.last_name == sample_user_data["last_name"]
    assert user_response.is_active == sample_user_data["is_active"]
    assert user_response.is_verified == sample_user_data["is_verified"]
    assert user_response.created_at == sample_user_data["created_at"]
    assert user_response.updated_at == sample_user_data["updated_at"]

    mock_verify_token.assert_called_once_with('validtoken')

def test_get_current_user_invalid_token(mock_verify_token):

    # Test get_current_user with invalid token

    mock_verify_token.return_value = None

    with pytest.raises(HTTPException) as e:
        get_current_user(token='invalidtoken')

    assert e.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert e.value.detail == 'Could not validate credentials'

    mock_verify_token.assert_called_once_with('invalidtoken')

def test_get_current_user_valid_token_incomplete_payload(mock_verify_token):

    # Return an empty dict simulating missing required fields

    mock_verify_token.return_value = {}

    with pytest.raises(HTTPException) as e:
        get_current_user(token='validtoken')

    assert e.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert e.value.detail == 'Could not validate credentials'

def test_get_current_active_user_active(mock_verify_token):

    # Test get_current_active_user with an active user

    mock_verify_token.return_value = sample_user_data

    current_user = get_current_user(token='validtoken')
    active_user = get_current_active_user(current_user=current_user)

    assert isinstance(active_user, UserResponse)
    assert active_user.is_active is True

def test_get_current_active_user_inactive(mock_verify_token):

    # Test get_current_active_user with an inactive user

    mock_verify_token.return_value = inactive_user_data

    current_user = get_current_user(token='validtoken')

    with pytest.raises(HTTPException) as e:
        get_current_active_user(current_user=current_user)

    assert e.value.status_code == status.HTTP_400_BAD_REQUEST
    assert e.value.detail == 'Inactive user'

def test_get_current_user_sub(mock_verify_token):

    # Test get_current_user when sub is returned by the verify

    return_value = {
        'sub': uuid4(),
    }

    mock_verify_token.return_value = return_value

    current_user = get_current_user(token='validtoken')

    assert current_user.id == return_value['sub']
    assert current_user.username == 'unknown'
    assert current_user.email == 'unknown@example.com'
    assert current_user.first_name == 'Unknown'
    assert current_user.last_name == 'User'
    assert current_user.is_active == True
    assert current_user.is_verified == False
    assert current_user.created_at is not None
    assert current_user.updated_at is not None

def test_get_current_user_empty_token(mock_verify_token):

    # Test get_current_user when token verify returns empty dict

    return_value = {}

    mock_verify_token.return_value = {}

    with pytest.raises(HTTPException) as e:
        get_current_user(token='validtoken')

    assert e.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert e.value.detail == 'Could not validate credentials'

def test_get_current_user_uuid_token(mock_verify_token):

    # Test get_current_user when token verify returns a dict with a UUID

    return_value = uuid4()

    mock_verify_token.return_value = return_value

    current_user = get_current_user(token='validtoken')

    assert current_user.id == return_value
    assert current_user.username == 'unknown'
    assert current_user.email == 'unknown@example.com'
    assert current_user.first_name == 'Unknown'
    assert current_user.last_name == 'User'
    assert current_user.is_active == True
    assert current_user.is_verified == False
    assert current_user.created_at is not None
    assert current_user.updated_at is not None

def test_get_current_user_str_token(mock_verify_token):

    # Test get_current_user when token verify returns a str

    mock_verify_token.return_value = 'xyz'

    with pytest.raises(HTTPException) as e:
        get_current_user(token='validtoken')

    assert e.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert e.value.detail == 'Could not validate credentials'
