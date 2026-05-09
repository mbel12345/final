from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    # Database settings
    DATABASE_URL: str = 'postgresql://postgres:postgres@localhost:5432/fastapi_db'
    DROP_DB: bool = True # Drop and re-create DB on startup / tests

    # JWT settings
    JWT_SECRET_KEY: str = 'super-secret-key-asdfasdfadfsafdasdfsadf'
    JWT_REFRESH_SECRET_KEY: str = 'super-secret-refresh-key-asdfasdfasdfsadfasdf'
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    BCRYPT_ROUNDS: int = 12

    # Load .env vars
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encodings='utf-8',
        extra='ignore',
    )

settings = Settings()
