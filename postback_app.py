# postback_app.py
from typing import Optional
import hmac
import hashlib
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from settings import settings
from db import get_session, get_user_by_click_id, User
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from bot import check_subscription, send_screen, evaluate_and_route
from keyboards import kb_access
from config_service import pb_secret, platinum_threshold, first_deposit_min


app = FastAPI(title="PocketAI Postbacks")

# бот для пушей из постбэков
bot_push = Bot(token=settings.TOKEN, default=DefaultBotProperties(parse_mode="HTML"))


# ---------- helpers: подпись редирект-ссылок ----------
async def sign(kind: str, click_id: str) -> str:
    secret = await pb_secret()
    return hmac.new(secret.encode(), f"{kind}:{click_id}".encode(), hashlib.sha256).hexdigest()


async def verify(kind: str, click_id: str, sig: str) -> bool:
    try:
        expected = await sign(kind, click_id)
        return hmac.compare_digest(expected, sig)
    except Exception:
        return False


# ---------- health ----------
@app.get("/")
async def root():
    return {"ok": True, "name": "pocketai-postbacks"}


# ---------- редиректы на реф-ссылки (короткие пути) ----------
@app.get("/r/{click_id}/{sig}")
async def r_short(click_id: str, sig: str):
    # то же, что /go/reg
    return await go_reg(click_id=click_id, sig=sig)


@app.get("/d/{click_id}/{sig}")
async def d_short(click_id: str, sig: str):
    # то же, что /go/dep
    return await go_dep(click_id=click_id, sig=sig)


# ---------- редиректы на реф-ссылки (совместимость со старым форматом) ----------
@app.get("/go/reg")
async def go_reg(click_id: str, sig: str):
    if not await verify("reg", click_id, sig):
        raise HTTPException(status_code=403, detail="bad signature")

    async with get_session() as session:
        user = await get_user_by_click_id(session, click_id)
        if not user:
            raise HTTPException(status_code=404, detail="user not found")

        base = settings.REF_REG_B if user.group_ab == "B" else settings.REF_REG_A
        parts = urlparse(base)
        q = dict(parse_qsl(parts.query, keep_blank_values=True))
        q["click_id"] = click_id  # прокидываем click_id в PP
        url = urlunparse(parts._replace(query=urlencode(q)))
        return RedirectResponse(url, status_code=307)


@app.get("/go/dep")
async def go_dep(click_id: str, sig: str):
    if not await verify("dep", click_id, sig):
        raise HTTPException(status_code=403, detail="bad signature")

    async with get_session() as session:
        user = await get_user_by_click_id(session, click_id)
        if not user:
            raise HTTPException(status_code=404, detail="user not found")

        base = settings.REF_DEP_B if user.group_ab == "B" else settings.REF_DEP_A
        parts = urlparse(base)
        q = dict(parse_qsl(parts.query, keep_blank_values=True))
        q["click_id"] = click_id
        url = urlunparse(parts._replace(query=urlencode(q)))
        return RedirectResponse(url, status_code=307)


# ---------- прием постбэков из PP ----------
@app.get("/pb")
async def pb(
    event: Optional[str] = None,
    click_id: Optional[str] = None,
    trader_id: Optional[str] = None,
    sumdep: Optional[float] = 0.0,
    t: Optional[str] = None,
):
    # секьюрность: секрет в t= должен совпадать
    secret = await pb_secret()
    if not t or t != secret:
        raise HTTPException(status_code=403, detail="forbidden")

    if not click_id:
        raise HTTPException(status_code=400, detail="missing click_id")

    async with get_session() as session:
        user: Optional[User] = await get_user_by_click_id(session, click_id)
        if not user:
            raise HTTPException(status_code=404, detail="user not found")

        changed = False
        ev = (event or "").lower().strip()

        # записываем trader_id один раз
        if trader_id and not user.trader_id:
            user.trader_id = trader_id
            changed = True

        # регистрация
        if ev in {"reg", "registration"}:
            if not user.is_registered:
                user.is_registered = True
                changed = True

        # депозиты
        amount = float(sumdep or 0)
        if ev in {"dep_first", "dep_repeat", "deposit", "dep"} or amount > 0:
            if amount > 0:
                user.total_deposits = (user.total_deposits or 0.0) + amount
                changed = True

            # первый деп — учитываем минимальный порог
            fdm = await first_deposit_min()
            if (not user.has_deposit) and (amount >= fdm):
                user.has_deposit = True
                changed = True

        if changed:
            await session.commit()

        # проверим подписку в канале (могла появиться за это время)
        try:
            subscribed = await check_subscription(bot_push, user.telegram_id)
        except Exception:
            subscribed = False

        if subscribed and not user.is_subscribed:
            user.is_subscribed = True
            await session.commit()

        # автобилдер экранов по состоянию (обновление шага/доступа)
        try:
            await evaluate_and_route(bot_push, user)
        except Exception:
            # не ломаем постбэк, если пуш не удался
            pass

        # platinum: один раз показать и запомнить уведомление
        th = await platinum_threshold()
        became_platinum = (not user.is_platinum) and ((user.total_deposits or 0) >= th)
        if became_platinum:
            user.is_platinum = True
            await session.commit()

        if user.is_platinum and (not user.platinum_notified):
            try:
                await send_screen(
                    bot_push,
                    user,
                    key="platinum",
                    title_key="platinum_title",
                    text_key="platinum_text",
                    markup=kb_access(user.language or "ru", vip=True),
                )
                user.platinum_notified = True
                await session.commit()
            except Exception:
                pass

        return {
            "ok": True,
            "event": event,
            "telegram_id": user.telegram_id,
            "is_registered": user.is_registered,
            "has_deposit": user.has_deposit,
            "total_deposits": user.total_deposits,
            "is_platinum": user.is_platinum,
        }
