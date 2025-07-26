import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Settings:
    load_dotenv()
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://admin:admin@localhost:5432/swipe"
    )
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    reftesh_token_expire_days: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "90"))
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")


settings = Settings()
