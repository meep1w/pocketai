import os
from dataclasses import dataclass
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(filename=".env"))

@dataclass
class Settings:
    TOKEN: str = os.getenv("TOKEN_BOT", "").strip()
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    CHANNEL_ID: int = int(os.getenv("CHANNEL_ID", "0"))
    CHANNEL_URL: str = os.getenv("CHANNEL_URL", "")

    MINI_APP: str = os.getenv("MINI_APP", "")
    MINI_APP_PLATINUM: str = os.getenv("MINI_APP_PLATINUM", "")

    REF_REG_A: str = os.getenv("REF_REG_A", "")
    REF_DEP_A: str = os.getenv("REF_DEP_A", "")
    REF_REG_B: str = os.getenv("REF_REG_B", "")
    REF_DEP_B: str = os.getenv("REF_DEP_B", "")

    SUPPORT_URL: str = os.getenv("SUPPORT_URL", "")

    PLATINUM_THRESHOLD: float = float(os.getenv("PLATINUM_THRESHOLD", "100"))
    FIRST_DEPOSIT_MIN: float = float(os.getenv("FIRST_DEPOSIT_MIN", "10"))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./pocketai.db")

    PUBLIC_BASE: str = os.getenv("PUBLIC_BASE", "http://127.0.0.1:8000")
    PB_SECRET: str = os.getenv("PB_SECRET", "supersecret123").strip()

settings = Settings()
