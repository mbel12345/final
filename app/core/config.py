from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    # Database settings
    DATABASE_URL: str = 'postgresql://postgres:postgres@localhost:5432/fastapi_db'

settings = Settings()
