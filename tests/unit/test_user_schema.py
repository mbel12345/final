import pytest

from pydantic import ValidationError

from app.schemas.user import (
    PasswordMixin,
    PasswordUpdate,
    UserBase,
    UserCreate,
    UserLogin,
)

def test_user_base_valid():

    # Test UserBase with valid data

    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'username': 'johndoe',
    }
    user = UserBase(**data)
    assert user.first_name == 'John'
    assert user.email == 'john.doe@example.com'

def test_user_base_invalid_email():

    # Test UserBase with invalid email

    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'invalid-email',
        'username': 'johndoe',
    }

    with pytest.raises(ValidationError):
        UserBase(**data)

def test_password_mixin_valid():

    # Test PasswordMixin with valid password

    data = {
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!',
    }
    password_mixin = PasswordMixin(**data)

def test_password_mixin_invalid_short_password():

    # Test that short passwords are rejected

    data = {
        'password': 'A2a!',
        'confirm_password': 'A2a!',
    }

    with pytest.raises(ValidationError, match=r'2 validation errors[\s\S]*password[\s\S]*String should have at least 8 characters[\s\S]*confirm_password[\s\S]*String should have at least 8 characters'):
        PasswordMixin(**data)

def test_password_mixin_no_uppercase():

    # Test that passwords with no uppercase letters are rejected

    data = {
        'password': 'securepass123!',
        'confirm_password': 'securepass123!',
    }

    with pytest.raises(ValidationError, match=r'1 validation error[\s\S]*Password must contain at least one uppercase letter'):
        PasswordMixin(**data)

def test_password_mixin_no_lowercase():

    # Test that passwords with no lowercase letters are rejected

    data = {
        'password': 'SECUREPASS123!',
        'confirm_password': 'SECUREPASS123!',
    }

    with pytest.raises(ValidationError, match=r'1 validation error[\s\S]*Password must contain at least one lowercase letter'):
        PasswordMixin(**data)

def test_password_mixin_no_digit():

    # Test that passwords with no digits are rejected

    data = {
        'password': 'SECUREpass!',
        'confirm_password': 'SECUREpass!',
    }

    with pytest.raises(ValidationError, match=r'1 validation error[\s\S]*Password must contain at least one digit'):
        PasswordMixin(**data)

def test_password_mixin_no_special_chars():

    # Test that passwords with no special characters are rejected

    data = {
        'password': 'SECUREpass123',
        'confirm_password': 'SECUREpass123',
    }

    with pytest.raises(ValidationError, match=r'1 validation error[\s\S]*Password must contain at least one special character'):
        PasswordMixin(**data)

def test_user_create_valid():

    # Test UserCreate with valid data

    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'username': 'johndoe',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!',
    }
    user_create = UserCreate(**data)
    assert user_create.username == 'johndoe'
    assert user_create.password == 'SecurePass123!'

def test_user_create_invalid_password():

    # Test UserCreate with invalid password

    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'username': 'johndoe',
        'password': 'SECUREpass!',
        'confirm_password': 'SECUREpass!',
    }

    with pytest.raises(ValidationError, match=r'1 validation error[\s\S]*Password must contain at least one digit'):
        UserCreate(**data)

def test_user_login_valid():

    # Test UserLogin with valid data

    data = {
        'username': 'johndoe',
        'password': 'SecurePass123',
    }
    user_login = UserLogin(**data)
    assert user_login.username == 'johndoe'

def test_user_login_invalid_username():

    # Test UserLogin with short username

    data = {
        'username': 'jo',
        'password': 'SecurePass123',
    }

    with pytest.raises(ValidationError, match=r'1 validation error for UserLogin[\s\S]*username[\s\S]*String should have at least 3 characters'):
        UserLogin(**data)

def test_user_login_invalid_password():

    # Test UserLogin with invalid password

    data = {
        'username': 'johndoe',
        'password': 'short',
    }

    with pytest.raises(ValidationError, match=r'1 validation error for UserLogin[\s\S]*password[\s\S]*String should have at least 8 characters'):
        UserLogin(**data)

def test_password_mixin_password_mismatch():

    # Test that PasswordMixin fails when password and confirmation do not match

    data = {
        'password': 'SECUREpass123!',
        'confirm_password': 'SECUREpass123456!',
    }

    with pytest.raises(ValidationError, match=r'1 validation error for PasswordMixin[\s\S]*Passwords do not match'):
        PasswordMixin(**data)


def test_password_update_valid():

    # Test that PasswordUpdate works with valid data

    data = {
        'current_password': 'OLDpass123!',
        'new_password': 'NEWpass123!',
        'confirm_new_password': 'NEWpass123!',
    }

    password_update = PasswordUpdate(**data)
    assert password_update.current_password == data['current_password']
    assert password_update.new_password == data['new_password']
    assert password_update.confirm_new_password == data['confirm_new_password']

def test_password_update_password_mismatch():

    # Test that PasswordUpdate fails when password and confirmation do not match

    data = {
        'current_password': 'OLDpass123!',
        'new_password': 'SECUREpass123!',
        'confirm_new_password': 'SECUREpass123456!',
    }

    with pytest.raises(ValidationError, match=r'1 validation error for PasswordUpdate[\s\S]*New password and confirmation do not match'):
        PasswordUpdate(**data)

def test_password_update_reject_reused_password():

    # Test that PasswordUpdate fails when new password is the same as current password

    data = {
        'current_password': 'OLDpass123!',
        'new_password': 'OLDpass123!',
        'confirm_new_password': 'OLDpass123!',
    }

    with pytest.raises(ValidationError, match=r'1 validation error for PasswordUpdate[\s\S]*New password must be different from current password'):
        PasswordUpdate(**data)
