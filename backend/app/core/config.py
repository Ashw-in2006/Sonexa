from functools import lru_cache
from os import getenv


@lru_cache
def get_settings() -> dict:
    allowed_origins = getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
    )
    return {
        "jamendo_client_id": getenv("JAMENDO_CLIENT_ID", ""),
        "jamendo_client_secret": getenv("JAMENDO_CLIENT_SECRET", ""),
        "allowed_origins": [origin.strip() for origin in allowed_origins.split(",") if origin.strip()],
    }
