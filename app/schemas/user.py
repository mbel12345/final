import uuid

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

class UserBase(BaseModel):

    # Base schema for User

    first_name: str = Field(
        min_length=1,
        max_length=50,
        example='John',
        description="User's first name",
    )

    last_name: str = Field(
        min_length=1,
        max_length=50,
        example='Doe',
        description="User's last name",
    )

    email: EmailStr = Field(
        example='john.doe@example.com',
        description="User's email address",
    )

    username: str = Field(
        min_length=3,
        max_length=50,
        example='johndoe',
        description="User's unique username",
    )

    model_config = ConfigDict(from_attributes=True)

class PasswordMixin(BaseModel):

    password: str = Field(
        min_length=8,
        max_length=128,
        example='SecurePass123!',
        description="User's password (8-128 characters)",
    )

    confirm_password: str = Field(
        min_length=8,
        max_length=128,
        example='SecurePass123!',
        description='Password confirmation',
    )

    @model_validator(mode='after')
    def verify_password_match(self) -> 'PasswordMixin':

        # Check that password and confirm_password match

        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')

        return self

    @model_validator(mode='after')
    def validate_password_strength(self) -> 'PasswordMixin':

        # Check for password strength requirements

        password = self.password
        if not any(char.isupper() for char in password):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in password):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isdigit() for char in password):
            raise ValueError('Password must contain at least one digit')
        if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in password):
            raise ValueError('Password must contain at least one special character')
        return self

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'username': 'johndoe',
                'password': 'SecurePass123!',
                'confirm_password': 'SecurePass123!',
            }
        }
    )

class UserCreate(UserBase, PasswordMixin):

    # Schema for User creation with password validation

   pass

class UserResponse(UserBase):

    # Schema for User Response

    id: uuid.UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

class UserLogin(BaseModel):

    # Schema for User Login

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        example='johndoe',
        description='Username or email',
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        example='SecurePass123!',
        description='Password',
    )

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'username': 'johndoe',
                'password': 'SecurePass123!',
            }
        }
    )

class UserUpdate(UserBase):

    # Schema for User Update
    pass

class PasswordUpdate(BaseModel):

    # Schema for password updates

    current_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        example='OldPass123!',
        description='Current password',
    )

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        example='NewPass123!',
        description='New password',
    )

    confirm_new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        example='NewPass123!',
        description='Confirm new password',
    )

    @model_validator(mode='after')
    def verify_passwords(self) -> 'PasswordUpdate':

        # Verify that the new password and confirmation are valid

        if self.new_password != self.confirm_new_password:
            raise ValueError('New password and confirmation do not match')
        if self.current_password == self.new_password:
            raise ValueError('New password must be different from current password')
        return self

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'current_password': 'OldPass123!',
                'new_password': 'NewPass123!',
                'confirm_new_password': 'NewPass123!'
            }
        }
    )
