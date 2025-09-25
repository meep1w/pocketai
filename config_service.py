from typing import Optional
from sqlalchemy import select
from db import get_session, Config
from settings import settings

async def get_value(key: str, default: Optional[str] = None) -> Optional[str]:
    async with get_session() as session:
        res = await session.execute(select(Config).where(Config.key == key))
        row = res.scalar_one_or_none()
        return row.value if row else default

async def set_value(key: str, value: str) -> None:
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
    return str(v).lower() in {"1","true","yes","on"}

async def set_bool(key: str, value: bool) -> None:
    await set_value(key, "1" if value else "0")

async def get_float(key: str, default: float) -> float:
    v = await get_value(key, None)
    try:
        return float(v) if v is not None else default
    except Exception:
        return default

async def set_float(key: str, value: float) -> None:
    await set_value(key, str(value))

# dynamic getters
async def pb_secret() -> str:
    return await get_value("PB_SECRET", settings.PB_SECRET)

async def ref_reg_a() -> str:
    return await get_value("REF_REG_A", settings.REF_REG_A)

async def ref_dep_a() -> str:
    return await get_value("REF_DEP_A", settings.REF_DEP_A)

async def channel_id() -> int:
    v = await get_value("CHANNEL_ID", None)
    return int(v) if v else settings.CHANNEL_ID

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

# Broadcast helpers
async def bcast_text() -> str:
    return await get_value("BCAST_TEXT", "") or ""

async def bcast_photo() -> str:
    return await get_value("BCAST_PHOTO", "") or ""

async def set_bcast_text(v: str) -> None:
    await set_value("BCAST_TEXT", v)

async def set_bcast_photo(v: str) -> None:
    await set_value("BCAST_PHOTO", v)
