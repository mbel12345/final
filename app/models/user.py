import uuid

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from sqlalchemy import Boolean, Column, DateTime, func, or_, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr, mapped_column, relationship

from app.auth.jwt import create_token
from app.auth.jwt import get_password_hash
from app.auth.jwt import verify_password
from app.core.config import settings
from app.database import Base
from app.schemas.token import TokenType

def utcnow():

    # Helper function get current UTC datetime

    return datetime.now(timezone.utc)

class User(Base):

    __tablename__ = 'users'

    @declared_attr
    def id(cls):

        return Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4, unique=True,
            index=True,
        )

    @declared_attr
    def username(cls):

        return Column(
            String(50),
            unique=True,
            nullable=False,
            index=True,
        )

    @declared_attr
    def email(cls):

        return Column(
            String, unique=True,
            nullable=False,
            index=True,
        )

    @declared_attr
    def password(cls):

        return Column(
            String,
            nullable=False,
        )


    @declared_attr
    def first_name(cls):

        return Column(
            String(50),
            nullable=False,
        )

    @declared_attr
    def last_name(cls):

        return Column(
            String(50),
            nullable=False,
        )

    @declared_attr
    def is_active(cls):

        return Column(
            Boolean,
            default=True,
        )

    @declared_attr
    def is_verified(cls):

        return Column(
            Boolean,
            default=False,
        )

    @declared_attr
    def created_at(cls):

        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls):

        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )

    @declared_attr
    def last_login(cls):

        return Column(
            DateTime(timezone=True),
            nullable=True,
        )

    calculations = relationship('Calculation', back_populates='user', cascade='all, delete-orphan')

    def __init__(self, *args, **kwargs):

        # Initialize a new user, handling hashed_password

        if 'hashed_password' in kwargs:
            kwargs['password'] = kwargs.pop('hashed_password')
        super().__init__(*args, **kwargs)

    def __repr__(self):

        # String representation of the user

        return f'<User(name={self.first_name} {self.last_name}, email={self.email})>'

    def update(self, **kwargs):

        # Update user attributes and ensure updated_at is refreshed

        for key, value in kwargs.items():
            setattr(self, key, value)
        self.updated_at = utcnow()

    @property
    def hashed_password(self):

        # Return the stored hashed password.

        return self.password

    def verify_password(self, plain_password: str)-> bool:

        # Verify a plain-text password against the stored hashed password

        return verify_password(plain_password, self.password)

    @classmethod
    def hash_password(cls, password: str) -> str:

        # Hash a plain-text password using the application's password hashing utility

        return get_password_hash(password)

    @classmethod
    def register(cls, db, user_data: dict):

        # Register a new user

        password = user_data.get('password')
        if not password or len(password) < 6:
            raise ValueError('Password must be at least 6 characters long')

        # Check for duplicate email or username
        existing_user = db.query(cls).filter(
            or_(
                cls.email == user_data['email'],
                cls.username == user_data['username'],
            )
        ).first()
        if existing_user:
            raise ValueError('Username or email already exists')

        # Create a new user instance
        hashed_password = cls.hash_password(password)
        user = cls(
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=user_data['email'],
            username=user_data['username'],
            password=hashed_password,
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        db.commit()
        return user

    @classmethod
    def authenticate(cls, db, username_or_email: str, password: str):

        # Authenticate a user by username/email and password

        user = db.query(cls).filter(
            or_(
                cls.username == username_or_email,
                cls.email == username_or_email,
            )
        ).first()

        if not user or not user.verify_password(password):
            return None

        # Update last_login
        user.last_login = utcnow()
        db.flush()

        # Generate tokens
        access_token = cls.create_access_token({'sub': str(user.id)})
        refresh_token = cls.create_refresh_token({'sub': str(user.id)})
        expires_at = utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_at': expires_at,
            'user': user,
        }

    @classmethod
    def create_access_token(cls, data: dict) -> str:

        # Create a JWT access token

        return create_token(data['sub'], TokenType.ACCESS)

    @classmethod
    def create_refresh_token(cls, data: dict) -> str:

        # Create a JWT refresh token

        return create_token(data['sub'], TokenType.REFRESH)

    @classmethod
    def verify_token(cls, token: str):

        # Verify a JWT token and return the user identifier

        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
            sub = payload.get('sub')
            if sub is None:
                return None
            try:
                return uuid.UUID(sub)
            except (TypeError, ValueError):
                return None
        except JWTError:
            return None
