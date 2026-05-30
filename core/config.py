from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    PASSWORD_MIN_LENGTH: int = 6
    OTP_EXPIRE_MINUTES: int = 5
    OTP_LENGTH: int = 6

    DATABASE_URL: str = "postgresql://uthau:uthau@localhost:5432/uthau"

    CORS_ORIGINS: List[str] = ["*"]
    ENVIRONMENT: str = "development"

    COMMISSION_PERCENT: float = 20.0

    NIGHT_SURGE_START: int = 21
    NIGHT_SURGE_END: int = 6
    NIGHT_SURGE_MULTIPLIER: float = 1.25

    APP_URL: str = "http://localhost:8002"
    CURRENCY: str = "NPR"
    CURRENCY_SYMBOL: str = "Rs."
    TIMEZONE: str = "Asia/Kathmandu"
    LANGUAGES: List[str] = ["ne", "en"]

    SMS_PROVIDER: str = "sparrow"
    SPARROW_SMS_TOKEN: str = ""
    SPARROW_SMS_FROM: str = "UTHAU"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
