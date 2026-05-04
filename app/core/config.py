from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    # Database settings
    DATABASE_URL: str = 'postgresql://postgres:postgres@localhost:5432/fastapi_db'

    # JWT settings
    JWT_SECRET_KEY: str = 'super-secret-key-asdfasdfadfsafdasdfsadf'
    JWT_REFRESH_SECRET_KEY: str = 'super-secret-refresh-key-asdfasdfasdfsadfasdf'
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    BCRYPT_ROUNDS: int = 12

settings = Settings()
