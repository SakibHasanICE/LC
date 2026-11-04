"""
Application configuration loaded from environment variables (.env file).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    # --- Email (IMAP) ---
    IMAP_HOST: str = os.getenv("IMAP_HOST", "")
    IMAP_PORT: int = int(os.getenv("IMAP_PORT", "993"))
    IMAP_USER: str = os.getenv("IMAP_USER", "")
    IMAP_PASSWORD: str = os.getenv("IMAP_PASSWORD", "")
    IMAP_FOLDER: str = os.getenv("IMAP_FOLDER", "INBOX")

    # --- Database ---
    DB_URL: str = os.getenv("DB_URL", "")

    # # --- LLM fallback extraction ---
    # LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    # LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

    # --- App ---
    ENV: str = os.getenv("ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        """Raise if required settings are missing. Call this once at startup."""
        required = {
            "IMAP_HOST": cls.IMAP_HOST,
            "IMAP_USER": cls.IMAP_USER,
            "IMAP_PASSWORD": cls.IMAP_PASSWORD,
            "DB_URL": cls.DB_URL,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}"
            )


settings = Settings()