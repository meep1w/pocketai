import asyncio
from pathlib import Path
from typing import Optional
import hmac, hashlib

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile

from sqlalchemy import select, func

from settings import settings
from db import (
    init_db, get_session, get_or_create_user, User,
    ensure_click_id, ContentOverride
)
from texts import t
from keyboards import (
    kb_main, kb_instruction, kb_lang, kb_subscribe,
    kb_register, kb_deposit, kb_access
)
from admin import router as admin_router
from config_service import (
    pb_secret, channel_id,
    first_deposit_min, platinum_threshold,
    check_subscription_enabled, check_registration_enabled, check_deposit_enabled
)

ASSETS = Path(__file__).parent / "assets"
DEFAULT_LANG = "en"


# ----------------- helpers -----------------
def user_lang(user: User) -> str:
    return user.language or DEFAULT_LANG


async def make_sig(kind: str, click_id: str) -> str:
    secret = await pb_secret()
    return hmac.new(secret.encode(), f"{kind}:{click_id}".encode(), hashlib.sha256).hexdigest()


def photo_path(lang: Optional[str], key: str) -> Optional[Path]:
    subdir = "ru" if (lang == "ru") else "en"
    p = ASSETS / subdir / f"{key}.jpg"
    return p if p.exists() else None


async def delete_previous(bot: Bot, chat_id: int, user: User) -> None:
    if user.last_bot_message_id:
        try:
            await bot.delete_message(chat_id, user.last_bot_message_id)
        except Exception:
            pass


async def send_screen(bot: Bot, user: User, key: str, title_key: str, text_key: str, markup) -> None:
    """Единая отправка экрана с авто-удалением предыдущего и учётом оверрайдов из админки."""
    async with get_session() as session:
        db_user = await session.get(User, user.id)
        await delete_previous(bot, db_user.telegram_id, db_user)

        lang = user_lang(db_user)
        img = photo_path(lang, key)

        # базовые тексты
        title = t(lang, title_key)
        body = t(lang, text_key)

        # оверрайды
        res = await session.execute(
            select(ContentOverride).where(ContentOverride.lang == lang, ContentOverride.screen == key)
        )
        ov = res.scalar_one_or_none()
        if ov:
            title = ov.title or title
            body = ov.text or body

        caption = f"<b>{title}</b>\n\n{body}"
        if img is not None:
            msg = await bot.send_photo(
                chat_id=db_user.telegram_id, photo=FSInputFile(img),
                caption=caption, parse_mode="HTML", reply_markup=markup
            )
        else:
            msg = await bot.send_message(
                chat_id=db_user.telegram_id, text=caption,
                parse_mode="HTML", reply_markup=markup
            )

        db_user.last_bot_message_id = msg.message_id
        await session.commit()


async def check_subscription(bot: Bot, tg_id: int) -> bool:
    try:
        cid = await channel_id()
        member = await bot.get_chat_member(cid, tg_id)
        status = getattr(member, "status", None)
        return status in {"member", "administrator", "creator"}
    except TelegramForbiddenError:
        return False
    except Exception:
        return False


async def evaluate_and_route(bot: Bot, user: User) -> None:
    """Показывает следующий актуальный экран по воронке."""
    async with get_session() as session:
        u = await session.get(User, user.id)

        # авто-обновление подписки
        is_sub = await check_subscription(bot, u.telegram_id)
        if is_sub and not u.is_subscribed:
            u.is_subscribed = True
            await session.commit()

        # 1) Подписка
        if await check_subscription_enabled():
            if not u.is_subscribed:
                await send_screen(
                    bot, u, key="subscribe",
                    title_key="subscribe_title", text_key="subscribe_text",
                    markup=kb_subscribe(user_lang(u))
                )
                return

        # 2) Регистрация
        if await check_registration_enabled():
            if not u.is_registered:
                u = await ensure_click_id(session, u)
                reg_url = f"{settings.PUBLIC_BASE.rstrip('/')}/r/{u.click_id}/{await make_sig('reg', u.click_id)}"
                await send_screen(
                    bot, u, key="register",
                    title_key="register_title", text_key="register_text",
                    markup=kb_register(user_lang(u), reg_url)
                )
                return

        # 3) Депозит
        if await check_deposit_enabled():
            if not u.has_deposit:
                u = await ensure_click_id(session, u)
                dep_url = f"{settings.PUBLIC_BASE.rstrip('/')}/d/{u.click_id}/{await make_sig('dep', u.click_id)}"
                await send_screen(
                    bot, u, key="deposit",
                    title_key="deposit_title", text_key="deposit_text",
                    markup=kb_deposit(user_lang(u), dep_url)
                )
                return

        # Platinum (защита от расхождений с постбэком)
        th = await platinum_threshold()
        if (not u.is_platinum) and (u.total_deposits >= th):
            u.is_platinum = True
            await session.commit()

        # Доступ открыт — пушим один раз
        if not u.access_notified:
            u.access_notified = True
            await session.commit()
            await send_screen(
                bot, u, key="access",
                title_key="access_title", text_key="access_text",
                markup=kb_access(user_lang(u), vip=u.is_platinum)
            )
            return


# ----------------- router -----------------
router = Router()


@router.message(Command("start"))
async def cmd_start(m: Message, bot: Bot):
    async with get_session() as session:
        user = await get_or_create_user(session, m.from_user.id)

        # первый старт — выбор языка (langs.jpg)
        if not user.language:
            await send_screen(
                bot, user, key="langs",
                title_key="lang_title", text_key="lang_title",
                markup=kb_lang(user_lang(user))
            )
            return

        # дальше — главное меню
        can_open = (user.is_subscribed and user.is_registered and user.has_deposit)
        await send_screen(
            bot, user, key="main",
            title_key="main_title", text_key="main_desc",
            markup=kb_main(user_lang(user), user.is_platinum, can_open)
        )


@router.callback_query(F.data == "menu")
async def cb_menu_user(c: CallbackQuery, bot: Bot):
    async with get_session() as session:
        user = await get_or_create_user(session, c.from_user.id)
        can_open = (user.is_subscribed and user.is_registered and user.has_deposit)
        await send_screen(
            bot, user, key="main",
            title_key="main_title", text_key="main_desc",
            markup=kb_main(user_lang(user), user.is_platinum, can_open)
        )
    await c.answer()


@router.callback_query(F.data == "instructions")
async def cb_instructions(c: CallbackQuery, bot: Bot):
    async with get_session() as session:
        user = await get_or_create_user(session, c.from_user.id)
        await send_screen(
            bot, user, key="instruction",
            title_key="instruction_title", text_key="instruction_text",
            markup=kb_instruction(user_lang(user))
        )
    await c.answer()


@router.callback_query(F.data == "lang")
async def cb_lang(c: CallbackQuery, bot: Bot):
    async with get_session() as session:
        user = await get_or_create_user(session, c.from_user.id)
        await send_screen(
            bot, user, key="langs",
            title_key="lang_title", text_key="lang_title",
            markup=kb_lang(user_lang(user))
        )
    await c.answer()


@router.callback_query(F.data.startswith("setlang:"))
async def cb_setlang(c: CallbackQuery, bot: Bot):
    lang = c.data.split(":", 1)[1]
    if lang not in {"ru", "en", "hi", "es"}:
        lang = DEFAULT_LANG
    async with get_session() as session:
        user = await get_or_create_user(session, c.from_user.id)
        user.language = lang
        await session.commit()

        can_open = (user.is_subscribed and user.is_registered and user.has_deposit)
        await send_screen(
            bot, user, key="main",
            title_key="main_title", text_key="main_desc",
            markup=kb_main(user_lang(user), user.is_platinum, can_open)
        )
    await c.answer()


@router.callback_query(F.data == "get_signal")
async def cb_get_signal(c: CallbackQuery, bot: Bot):
    async with get_session() as session:
        user = await get_or_create_user(session, c.from_user.id)
    await evaluate_and_route(bot, user)
    await c.answer()


# «Я подписался» на шаге подписки
@router.callback_query(F.data == "check_sub")
async def on_check_subscription(c: CallbackQuery, bot: Bot):
    async with get_session() as session:
        user = await get_or_create_user(session, c.from_user.id)

        is_sub = await check_subscription(bot, user.telegram_id)
        if is_sub and not user.is_subscribed:
            user.is_subscribed = True
            await session.commit()

        # просто двигаем дальше по воронке (и покажем алерт в evaluate, если нужно)
        await evaluate_and_route(bot, user)
    await c.answer()


# Кнопка регистрации из инструкции (callback)
@router.callback_query(F.data == "btn_register")
async def on_btn_register(c: CallbackQuery, bot: Bot):
    async with get_session() as session:
        user = await get_or_create_user(session, c.from_user.id)
        lang = user_lang(user)

        if user.is_registered:
            await c.answer(t(lang, "already_registered"), show_alert=True)
            return

        user = await ensure_click_id(session, user)
        reg_url = f"{settings.PUBLIC_BASE.rstrip('/')}/r/{user.click_id}/{await make_sig('reg', user.click_id)}"
        await send_screen(
            bot, user, key="register",
            title_key="register_title", text_key="register_text",
            markup=kb_register(lang, reg_url)
        )
    await c.answer()


@router.message(Command("whoami"))
async def cmd_whoami(m: Message):
    async with get_session() as session:
        res = await session.execute(select(User).where(User.telegram_id == m.from_user.id))
        u = res.scalar_one_or_none()
        if not u:
            await m.answer("no user in db yet")
            return
        await m.answer(
            "tg_id: {}\n"
            "group: {}\n"
            "lang: {}\n"
            "subscribed: {}\n"
            "registered: {}\n"
            "has_deposit: {}\n"
            "total_deposits: {}\n"
            "platinum: {}\n"
            "click_id: {}\n"
            "trader_id: {}".format(
                u.telegram_id, u.group_ab, u.language,
                u.is_subscribed, u.is_registered, u.has_deposit,
                u.total_deposits, u.is_platinum, u.click_id, u.trader_id
            )
        )


# ----------------- entry -----------------
async def main() -> None:
    await init_db()
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(admin_router)
    bot = Bot(token=settings.TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    print("Bot started …")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
