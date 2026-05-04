import uuid

from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.models.user import User
from app.schemas.user import UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')

def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> UserResponse:

    # Get the current user from the JWT token

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    token_data = User.verify_token(token)
    if token_data is None:
        raise credentials_exception

    try:
        if isinstance(token_data, dict):
            if 'username' in token_data:
                return UserResponse(**token_data)
            elif 'sub' in token_data:
                return UserResponse(
                    id=token_data['sub'],
                    username='unknown',
                    email='unknown@example.com',
                    first_name='Unknown',
                    last_name='User',
                    is_active=True,
                    is_verified=False,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            else:
                raise credentials_exception

        elif isinstance(token_data, uuid.UUID):

            return UserResponse(
                id=token_data,
                username='unknown',
                email='unknown@example.com',
                first_name='Unknown',
                last_name='User',
                is_active=True,
                is_verified=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

        else:
            raise credentials_exception

    except Exception as e:
        raise credentials_exception

def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:

    # Dependency to ensure that the current user is active

    if not current_user.is_active:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Inactive user',
        )

    return current_user
