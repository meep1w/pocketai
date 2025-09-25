from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Integer, String, Boolean, Float, select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from settings import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    language: Mapped[Optional[str]] = mapped_column(String(2), default=None)
    group_ab: Mapped[str] = mapped_column(String(1), default='A')

    click_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True, nullable=True)
    trader_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)

    is_subscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    has_deposit: Mapped[bool] = mapped_column(Boolean, default=False)

    total_deposits: Mapped[float] = mapped_column(Float, default=0.0)
    is_platinum: Mapped[bool] = mapped_column(Boolean, default=False)

    access_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    platinum_notified: Mapped[bool] = mapped_column(Boolean, default=False)

    last_bot_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class Config(Base):
    __tablename__ = "config"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(4096), nullable=False)

class ContentOverride(Base):
    __tablename__ = "content_overrides"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lang: Mapped[str] = mapped_column(String(2), index=True)
    screen: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    text: Mapped[Optional[str]] = mapped_column(String(4096), nullable=True)

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def get_session() -> AsyncSession:
    return AsyncSessionLocal()

def gen_click_id() -> str:
    from uuid import uuid4
    return uuid4().hex

async def ensure_click_id(session: AsyncSession, user: "User") -> "User":
    if not user.click_id:
        user.click_id = gen_click_id()
        await session.commit()
        await session.refresh(user)
    return user

from sqlalchemy import select

async def get_user_by_click_id(session: AsyncSession, click_id: str) -> Optional["User"]:
    result = await session.execute(select(User).where(User.click_id == click_id))
    return result.scalar_one_or_none()

async def get_or_create_user(session: AsyncSession, tg_id: int) -> "User":
    result = await session.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalar_one_or_none()
    if user:
        return user
    total = await session.scalar(select(func.count(User.id)))
    next_index = (total or 0) + 1
    group = 'B' if (next_index % 3 == 0) else 'A'
    user = User(telegram_id=tg_id, group_ab=group)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
