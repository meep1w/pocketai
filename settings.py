import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

DEFAULT_LANG = os.getenv('DEFAULT_LANG', 'en')

@dataclass
class Settings:
    # Telegram / доступ
    TOKEN: str = os.getenv("TOKEN_BOT", "").strip()

    # совместимость со старым ADMIN_ID (один админ)
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0") or 0)

    # новый формат: несколько админов через запятую
    ADMIN_IDS: list[int] = field(default_factory=list)

    CHANNEL_ID: int = int(os.getenv("CHANNEL_ID", "0") or 0)
    CHANNEL_URL: str = os.getenv("CHANNEL_URL", "").strip()

    # Публичный базовый URL (для красивых ссылок и постбэков)
    PUBLIC_BASE: str = os.getenv("PUBLIC_BASE", "").strip().rstrip("/")

    # Мини-аппы
    MINI_APP: str = os.getenv("MINI_APP", "").strip()
    MINI_APP_PLATINUM: str = os.getenv("MINI_APP_PLATINUM", "").strip()

    # Рефы A/B
    REF_REG_A: str = os.getenv("REF_REG_A", "").strip()
    REF_DEP_A: str = os.getenv("REF_DEP_A", "").strip()
    REF_REG_B: str = os.getenv("REF_REG_B", "").strip()
    REF_DEP_B: str = os.getenv("REF_DEP_B", "").strip()

    SUPPORT_URL: str = os.getenv("SUPPORT_URL", "").strip()

    # Пороги
    PLATINUM_THRESHOLD: float = float(os.getenv("PLATINUM_THRESHOLD", "100"))
    FIRST_DEPOSIT_MIN: float = float(os.getenv("FIRST_DEPOSIT_MIN", "10"))

    # Секрет постбэков
    PB_SECRET: str = os.getenv("PB_SECRET", "supersecret123").strip()

    # БД
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./pocketai.db")

    @property
    def PRIMARY_ADMIN(self) -> int:
        """
        Первый админ из списка (для deep-link 'Поддержка' и т.п.)
        """
        ids = self.ADMIN_IDS or ([self.ADMIN_ID] if self.ADMIN_ID else [])
        return ids[0] if ids else 0


settings = Settings()

# распарсим ADMIN_IDS из .env
_raw = os.getenv("ADMIN_IDS", "").replace(";", ",")
ids: list[int] = []
for part in _raw.split(","):
    part = part.strip()
    if part.isdigit():
        ids.append(int(part))
if not ids and settings.ADMIN_ID:
    ids = [settings.ADMIN_ID]
settings.ADMIN_IDS = ids
