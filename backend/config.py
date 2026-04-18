from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./guardcharge.db"
    CERTS_DIR: str = "certs"
    LOG_LEVEL: str = "INFO"

settings = Settings()