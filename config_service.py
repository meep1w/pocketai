from __future__ import annotations

from typing import Optional,Dict, Tuple
from sqlalchemy import select, delete

from db import get_session, Config, BtnOverride
from settings import settings

# in-memory кэш: {(lang, key): text}
BTN_CACHE: Dict[Tuple[str, str], str] = {}

# ========= базовые helpers =========

async def get_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Читает значение из таблицы Config. Если ключа нет — возвращает default.
    """
    async with get_session() as session:
        res = await session.execute(select(Config).where(Config.key == key))
        row = res.scalar_one_or_none()
        return row.value if row else default


async def set_value(key: str, value: str) -> None:
    """
    Пишет/обновляет значение в таблице Config.
    """
    async with get_session() as session:
        res = await session.execute(select(Config).where(Config.key == key))
        row = res.scalar_one_or_none()
        if row:
            row.value = value
        else:
            row = Config(key=key, value=value)
            session.add(row)
        await session.commit()


async def get_bool(key: str, default: bool) -> bool:
    v = await get_value(key, "1" if default else "0")
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


async def set_bool(key: str, value: bool) -> None:
    await set_value(key, "1" if value else "0")


async def get_float(key: str, default: float) -> float:
    v = await get_value(key, None)
    try:
        return float(v) if v is not None and str(v).strip() != "" else default
    except Exception:
        return default


async def set_float(key: str, value: float) -> None:
    await set_value(key, str(value))


# — вспомогательный безопасный парсер int —
async def _get_int(key: str, default: Optional[int] = None) -> Optional[int]:
    """
    Безопасно читает int из Config; если пусто — пробует взять из settings.
    Любая нечисловая строка -> default.
    """
    v = await get_value(key, None)
    if v is None or str(v).strip() == "":
        v = getattr(settings, key, None)
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return default


# ========= динамические геттеры, которые учитывают overrides из БД =========

async def pb_secret() -> str:
    return await get_value("PB_SECRET", settings.PB_SECRET)


async def ref_reg_a() -> str:
    return await get_value("REF_REG_A", settings.REF_REG_A)


async def ref_dep_a() -> str:
    return await get_value("REF_DEP_A", settings.REF_DEP_A)


async def channel_id() -> Optional[int]:
    """
    Возвращает числовой ID канала (может быть None, если значение мусорное/не задано).
    """
    return await _get_int("CHANNEL_ID", None)


async def channel_url() -> str:
    return await get_value("CHANNEL_URL", settings.CHANNEL_URL)


async def support_url() -> str:
    return await get_value("SUPPORT_URL", settings.SUPPORT_URL)


async def platinum_threshold() -> float:
    return await get_float("PLATINUM_THRESHOLD", settings.PLATINUM_THRESHOLD)


async def first_deposit_min() -> float:
    return await get_float("FIRST_DEPOSIT_MIN", settings.FIRST_DEPOSIT_MIN)


async def check_subscription_enabled() -> bool:
    return await get_bool("CHECK_SUBSCRIPTION", True)


async def check_registration_enabled() -> bool:
    return await get_bool("CHECK_REGISTRATION", True)


async def check_deposit_enabled() -> bool:
    return await get_bool("CHECK_DEPOSIT", True)


# ========= helpers для рассылки =========

async def bcast_text() -> str:
    return await get_value("BCAST_TEXT", "") or ""


async def bcast_photo() -> str:
    return await get_value("BCAST_PHOTO", "") or ""


async def set_bcast_text(v: str) -> None:
    await set_value("BCAST_TEXT", v)


async def set_bcast_photo(v: str) -> None:
    await set_value("BCAST_PHOTO", v)


async def load_button_overrides() -> None:
    async with get_session() as s:
        res = await s.execute(select(BtnOverride))
        BTN_CACHE.clear()
        for row in res.scalars():
            BTN_CACHE[(row.lang, row.key)] = row.text

def btn_text_cached(lang: str, key: str, default: str) -> str:
    """Синхронный доступ к кэшу: если нет override — вернём default."""
    return BTN_CACHE.get((lang, key), default)

async def set_btn_text(lang: str, key: str, value: str) -> None:
    async with get_session() as s:
        res = await s.execute(
            select(BtnOverride).where(BtnOverride.lang == lang, BtnOverride.key == key)
        )
        row = res.scalar_one_or_none()
        if row:
            row.text = value
        else:
            s.add(BtnOverride(lang=lang, key=key, text=value))
        await s.commit()
    BTN_CACHE[(lang, key)] = value

async def del_btn_text(lang: str, key: str) -> None:
    async with get_session() as s:
        await s.execute(delete(BtnOverride).where(
            BtnOverride.lang == lang, BtnOverride.key == key
        ))
        await s.commit()
    BTN_CACHE.pop((lang, key), None)