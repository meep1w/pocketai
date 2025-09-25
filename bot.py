import asyncio
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import hmac, hashlib

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile

from sqlalchemy import select, func

from settings import settings
from db import init_db, get_session, get_or_create_user, User, AsyncSession, ensure_click_id, ContentOverride
from texts import t
from keyboards import kb_main, kb_instruction, kb_lang, kb_subscribe, kb_register, kb_deposit, kb_access
from admin import router as admin_router
from config_service import pb_secret, channel_id, channel_url, ref_reg_a, ref_dep_a, first_deposit_min, platinum_threshold, check_subscription_enabled, check_registration_enabled, check_deposit_enabled

ASSETS = Path(__file__).parent / 'assets'

def with_params(url: str, **params) -> str:
    parts = urlparse(url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    q.update({k: str(v) for k, v in params.items() if v is not None})
    new_query = urlencode(q)
    return urlunparse(parts._replace(query=new_query))

async def make_sig(kind: str, click_id: str) -> str:
    secret = await pb_secret()
    return hmac.new(secret.encode(), f"{kind}:{click_id}".encode(), hashlib.sha256).hexdigest()

def photo_path(lang: Optional[str], key: str) -> Optional[Path]:
    subdir = 'ru' if (lang == 'ru') else 'en'
    p = ASSETS / subdir / f"{key}.jpg"
    return p if p.exists() else None

async def delete_previous(bot: Bot, chat_id: int, user: User) -> None:
    if user.last_bot_message_id:
        try:
            await bot.delete_message(chat_id, user.last_bot_message_id)
        except Exception:
            pass

async def send_screen(bot: Bot, user: User, key: str, title_key: str, text_key: str, markup) -> None:
    async with get_session() as session:
        db_user = await session.get(User, user.id)
        await delete_previous(bot, db_user.telegram_id, db_user)
        lang = db_user.language or 'ru'
        p = photo_path(lang, key)
        title = t(lang, title_key); body = t(lang, text_key)
        from sqlalchemy import select
        async with get_session() as s2:
            res = await s2.execute(select(ContentOverride).where(ContentOverride.lang==lang, ContentOverride.screen==key))
            ov = res.scalar_one_or_none()
        if ov:
            title = ov.title or title
            body = ov.text or body
        caption = f"<b>{title}</b>\n\n{body}"
        if p is not None:
            msg = await bot.send_photo(chat_id=db_user.telegram_id, photo=FSInputFile(p), caption=caption, parse_mode='HTML', reply_markup=markup)
        else:
            msg = await bot.send_message(chat_id=db_user.telegram_id, text=caption, parse_mode='HTML', reply_markup=markup)
        db_user.last_bot_message_id = msg.message_id
        await session.commit()

async def check_subscription(bot: Bot, tg_id: int) -> bool:
    try:
        cid = await channel_id()
        member = await bot.get_chat_member(cid, tg_id)
        status = getattr(member, 'status', None)
        return status in {"member", "administrator", "creator"}
    except TelegramForbiddenError:
        return False
    except Exception:
        return False

async def evaluate_and_route(bot: Bot, user: User) -> None:
    async with get_session() as session:
        u = await session.get(User, user.id)

        subscribed = await check_subscription(bot, u.telegram_id)
        if subscribed and not u.is_subscribed:
            u.is_subscribed = True
            await session.commit()

        if await check_subscription_enabled():
            if not u.is_subscribed:
                await send_screen(bot, u, key='subscribe', title_key='subscribe_title', text_key='subscribe_text', markup=kb_subscribe(u.language or 'ru'))
                return

        if await check_registration_enabled():
            if not u.is_registered:
                u = await ensure_click_id(session, u)
                reg_url = settings.PUBLIC_BASE.rstrip('/') + '/go/reg'
                reg_url = with_params(reg_url, click_id=u.click_id, sig=(await make_sig('reg', u.click_id)))
                await send_screen(bot, u, key='register', title_key='register_title', text_key='register_text', markup=kb_register(u.language or 'ru', reg_url))
                return

        if await check_deposit_enabled():
            if not u.has_deposit:
                u = await ensure_click_id(session, u)
                dep_url = settings.PUBLIC_BASE.rstrip('/') + '/go/dep'
                dep_url = with_params(dep_url, click_id=u.click_id, sig=(await make_sig('dep', u.click_id)))
                await send_screen(bot, u, key='deposit', title_key='deposit_title', text_key='deposit_text', markup=kb_deposit(u.language or 'ru', dep_url))
                return

        th = await platinum_threshold()
        if (not u.is_platinum) and (u.total_deposits >= th):
            u.is_platinum = True
            await session.commit()

        if not u.access_notified:
            u.access_notified = True
            await session.commit()
            await send_screen(bot, u, key='access', title_key='access_title', text_key='access_text', markup=kb_access(u.language or 'ru', vip=u.is_platinum))
            return

router = Router()

@router.message(Command("start"))
async def cmd_start(m: Message, bot: Bot):
    async with get_session() as session:
        user = await get_or_create_user(session, m.from_user.id)
        if not user.language:
            await send_screen(bot, user, key='main', title_key='lang_title', text_key='lang_title', markup=kb_lang())
            return
        can_open = (user.is_subscribed and user.is_registered and user.has_deposit)
        await send_screen(bot, user, key='main', title_key='main_title', text_key='main_desc', markup=kb_main(user.language, user.is_platinum, can_open))

@router.callback_query(F.data == 'menu')
async def cb_menu_user(c: CallbackQuery, bot: Bot):
    async with get_session() as session:
        user = await get_or_create_user(session, c.from_user.id)
        lang = user.language or 'ru'
        can_open = (user.is_subscribed and user.is_registered and user.has_deposit)
        await send_screen(bot, user, key='main', title_key='main_title', text_key='main_desc', markup=kb_main(lang, user.is_platinum, can_open))
        await c.answer()

@router.callback_query(F.data == 'instructions')
async def cb_instructions(c: CallbackQuery, bot: Bot):
    async with get_session() as session:
        user = await get_or_create_user(session, c.from_user.id)
        lang = user.language or 'ru'
        user = await ensure_click_id(session, user)
        reg_url = settings.PUBLIC_BASE.rstrip('/') + '/go/reg'
        reg_url = with_params(reg_url, click_id=user.click_id, sig=(await make_sig('reg', user.click_id)))
        await send_screen(bot, user, key='instruction', title_key='instruction_title', text_key='instruction_text', markup=kb_instruction(lang, reg_url))
        await c.answer()

@router.callback_query(F.data == 'lang')
async def cb_lang(c: CallbackQuery, bot: Bot):
    async with get_session() as session:
        user = await get_or_create_user(session, c.from_user.id)
        await send_screen(bot, user, key='main', title_key='lang_title', text_key='lang_title', markup=kb_lang())
        await c.answer()

@router.callback_query(F.data.startswith('setlang:'))
async def cb_setlang(c: CallbackQuery, bot: Bot):
    lang = c.data.split(':', 1)[1]
    if lang not in {'ru', 'en', 'hi', 'es'}:
        lang = 'en'
    async with get_session() as session:
        user = await get_or_create_user(session, c.from_user.id)
        user.language = lang
        await session.commit()
        can_open = (user.is_subscribed and user.is_registered and user.has_deposit)
        await send_screen(bot, user, key='main', title_key='main_title', text_key='main_desc', markup=kb_main(lang, user.is_platinum, can_open))
        await c.answer()

@router.callback_query(F.data == 'get_signal')
async def cb_get_signal(c: CallbackQuery, bot: Bot):
    async with get_session() as session:
        user = await get_or_create_user(session, c.from_user.id)
    await evaluate_and_route(bot, user)
    await c.answer()

@router.message(Command("whoami"))
async def cmd_whoami(m: Message):
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.telegram_id == m.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            await m.answer("no user in db yet")
            return
        await m.answer(
            f"tg_id: {user.telegram_id}\n"
            f"group: {user.group_ab}\n"
            f"lang: {user.language}\n"
            f"subscribed: {user.is_subscribed}\n"
            f"registered: {user.is_registered}\n"
            f"has_deposit: {user.has_deposit}\n"
            f"total_deposits: {user.total_deposits}\n"
            f"platinum: {user.is_platinum}\n"
            f"click_id: {user.click_id}\n"
            f"trader_id: {user.trader_id}"
        )

async def main() -> None:
    await init_db()
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(admin_router)
    bot = Bot(token=settings.TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    print("Bot started …")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
