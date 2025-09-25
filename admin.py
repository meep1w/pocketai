import asyncio
from pathlib import Path
from html import escape as h

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy import select, func

from settings import settings
from db import get_session, User, ContentOverride
from admin_keyboards import (
    kb_admin_menu, kb_users_list, kb_user_card, kb_links_menu,
    kb_content_lang, kb_content_screens, kb_content_editor,
    kb_params, kb_broadcast, kb_number_back
)
from config_service import (
    set_value, get_value, set_bool,
    pb_secret, ref_reg_a, ref_dep_a, channel_id, channel_url, support_url,
    platinum_threshold, first_deposit_min,
    bcast_text, bcast_photo, set_bcast_text, set_bcast_photo,
    check_subscription_enabled, check_registration_enabled, check_deposit_enabled,
)

router = Router(name="admin")


# --- helpers
def is_admin(user_id: int) -> bool:
    ids = getattr(settings, "ADMIN_IDS", []) or [settings.ADMIN_ID]
    return user_id in ids


async def _links_text() -> str:
    refreg = await ref_reg_a()
    refdep = await ref_dep_a()
    ch_id = await channel_id()
    ch_url = await channel_url()
    sup = await support_url()
    return (
        "🔗 <b>Ссылки</b>\n\n"
        f"Ref:\n<code>{h(refreg or '')}</code>\n\n"
        f"Deposit:\n<code>{h(refdep or '')}</code>\n\n"
        f"Channel ID: <code>{h(str(ch_id) if ch_id is not None else '')}</code>\n"
        f"Channel URL: {h(ch_url or '-')}\n"
        f"Support URL: {h(sup or '-')}\n"
    )


# --- entry
@router.message(Command("admin"))
async def cmd_admin(m: Message):
    if not is_admin(m.from_user.id):
        return
    await m.answer("<b>Панель администратора</b>", reply_markup=kb_admin_menu(), parse_mode='HTML')


@router.callback_query(F.data == "adm:menu")
async def cb_menu(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    await c.message.edit_text("<b>Панель администратора</b>", reply_markup=kb_admin_menu(), parse_mode='HTML')
    await c.answer()


# --- users (only group A, B never shown)
PER_PAGE = 20

@router.callback_query(F.data.startswith("adm:users:"))
async def cb_users(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    page = max(1, int(c.data.split(":")[2]))
    offset = (page - 1) * PER_PAGE

    async with get_session() as session:
        total = await session.scalar(select(func.count(User.id)).where(User.group_ab == 'A'))
        result = await session.execute(
            select(User).where(User.group_ab == 'A').order_by(User.id.desc()).offset(offset).limit(PER_PAGE)
        )
        rows = result.scalars().all()

    items = []
    for u in rows:
        r = '✅' if u.is_registered else '❌'
        d = '✅' if u.has_deposit else '❌'
        p = '💎' if u.is_platinum else ''
        items.append((u.telegram_id, f"{u.telegram_id}  R:{r}  D:{d}  {p}"))

    has_prev = page > 1
    has_next = total > offset + len(rows)

    await c.message.edit_text(
        f"👤 Пользователи ({total})\nВыберите пользователя:",
        reply_markup=kb_users_list(items, page, has_prev, has_next),
        parse_mode='HTML'
    )
    await c.answer()


@router.callback_query(F.data.startswith("adm:user:"))
async def cb_user_card(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return

    parts = c.data.split(":")
    action = parts[2]

    # toggle handlers
    if action in {"toggle"}:
        what = parts[3]
        tg_id = int(parts[4])
        async with get_session() as session:
            res = await session.execute(select(User).where(User.telegram_id == tg_id, User.group_ab == 'A'))
            u = res.scalar_one_or_none()
            if not u:
                await c.answer("Пользователь не найден", show_alert=True)
                return

            if what == "reg":
                u.is_registered = not u.is_registered
                if not u.is_registered:
                    u.access_notified = False
            elif what == "dep":
                u.has_deposit = not u.has_deposit
                if not u.has_deposit:
                    u.access_notified = False
            elif what == "plat":
                u.is_platinum = not u.is_platinum
                if not u.is_platinum:
                    u.platinum_notified = False

            await session.commit()

        # fallthrough to redraw card
        parts = ["adm", "user", str(tg_id)]

    # show card
    tg_id = int(parts[2])
    async with get_session() as session:
        res = await session.execute(select(User).where(User.telegram_id == tg_id, User.group_ab == 'A'))
        u = res.scalar_one_or_none()

    if not u:
        await c.answer("Пользователь не найден", show_alert=True)
        return

    text = (
        f"🪪 <b>Карточка пользователя</b>\n\n"
        f"TG ID: <code>{u.telegram_id}</code>\n"
        f"Язык: {u.language or '-' }\n"
        f"Click ID: <code>{u.click_id or '-'}</code>\n"
        f"Trader ID: <code>{u.trader_id or '-'}</code>\n\n"
        f"Регистрация: {'✅' if u.is_registered else '❌'}\n"
        f"Депозит (факт): {'✅' if u.has_deposit else '❌'}\n"
        f"Сумма депозитов: {u.total_deposits or 0:.2f}\n"
        f"Platinum: {'💎' if u.is_platinum else '•'}\n"
        f"Создан: {u.created_at:%Y-%m-%d %H:%M}"
    )

    await c.message.edit_text(
        text,
        reply_markup=kb_user_card(u.telegram_id, u.is_registered, u.has_deposit, u.is_platinum),
        parse_mode='HTML'
    )
    await c.answer()


# --- postbacks (helper text with code blocks)
@router.callback_query(F.data == "adm:postbacks")
async def cb_postbacks(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return

    secret = await pb_secret()
    base = (settings.PUBLIC_BASE or "").rstrip("/") or "https://YOUR_PUBLIC_HOST"

    reg = f"{base}/pb?event=reg&t={secret}&click_id={{click_id}}&trader_id={{trader_id}}"
    dep_first = f"{base}/pb?event=dep_first&t={secret}&click_id={{click_id}}&trader_id={{trader_id}}&sumdep={{sumdep}}"
    dep_repeat = f"{base}/pb?event=dep_repeat&t={secret}&click_id={{click_id}}&trader_id={{trader_id}}&sumdep={{sumdep}}"

    text = (
        "✏️ <b>Настройка постбэков</b>\n\n"
        "Вставьте эти URL в кабинете партнёрки (PocketPartners).\n"
        "Обязательно включите макросы: <code>{click_id}</code>, <code>{trader_id}</code>, <code>{sumdep}</code>.\n\n"
        "<b>Регистрация</b>\n"
        f"<code>{h(reg)}</code>\n\n"
        "<b>Первый депозит</b>\n"
        f"<code>{h(dep_first)}</code>\n\n"
        "<b>Повторный депозит</b>\n"
        f"<code>{h(dep_repeat)}</code>\n\n"
        "• <code>click_id</code> → <i>click_id</i>\n"
        "• <code>trader_id</code> → <i>trader_id</i>\n"
        "• <code>sumdep</code> → <i>sumdep</i>"
    )

    await c.message.edit_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=kb_admin_menu()
    )
    await c.answer()


# --- links (only A; prompt as new message + approval)
class EditState(StatesGroup):
    waiting_value = State()

@router.callback_query(F.data == "adm:links")
async def cb_links(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        return

    # читаем СЫРЫЕ значения из config, без подстановок из .env
    refreg = await get_value("REF_REG_A", "") or "-"
    refdep = await get_value("REF_DEP_A", "") or "-"
    ch_id  = await get_value("CHANNEL_ID", "") or "-"
    ch_url = await get_value("CHANNEL_URL", "") or "-"
    sup    = await get_value("SUPPORT_URL", "") or "-"

    text = (
        "🔗 <b>Ссылки</b>\n\n"
        f"Ref:\n<code>{refreg}</code>\n\n"
        f"Deposit:\n<code>{refdep}</code>\n\n"
        f"Channel ID: <code>{ch_id}</code>\n"
        f"Channel URL: {ch_url}\n"
        f"Support URL: {sup}\n"
    )
    await c.message.edit_text(text, reply_markup=kb_links_menu(), parse_mode='HTML')
    await c.answer()
    await state.clear()


@router.callback_query(F.data.startswith("adm:links:edit:"))
async def cb_links_edit(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        return
    key = c.data.split(":")[-1]
    await state.update_data(edit_key=key)

    prompts = {
        "REF_REG_A": "Введи новую реф-ссылку:",
        "REF_DEP_A": "Введи новую ссылку депозита:",
        "CHANNEL_ID": "Введи новый Channel ID (число):",
        "CHANNEL_URL": "Введи новый Channel URL (http/https):",
        "SUPPORT_URL": "Введи новый Support URL:",
    }
    # отправляем НОВОЕ сообщение (старое не затираем)
    await c.message.answer("✏️ " + prompts[key])
    await state.set_state(EditState.waiting_value)
    await c.answer()

@router.message(EditState.waiting_value)
async def on_edit_value(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    data = await state.get_data()
    key = data.get("edit_key")
    val = (m.text or "").strip()
    if not key:
        await m.answer("Неизвестный ключ")
        await state.clear()
        return

    await set_value(key, val)
    await m.answer("✅ Сохранено")
    # покажем обновлённый экран ссылок
    text = await _links_text()
    await m.answer(text, reply_markup=kb_links_menu(), parse_mode='HTML')
    await state.clear()


# --- content editor
@router.callback_query(F.data == "adm:content")
async def cb_content(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    await c.message.edit_text("🧩 Редактор контента — выберите язык", reply_markup=kb_content_lang())
    await c.answer()

@router.callback_query(F.data.startswith("adm:content:lang:"))
async def cb_content_lang(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    lang = c.data.split(":")[-1]
    await c.message.edit_text(f"Язык: {lang.upper()}\nВыберите экран:", reply_markup=kb_content_screens(lang))
    await c.answer()

SCREEN_MAP = {
    'main': ('main_title', 'main_desc'),
    'instruction': ('instruction_title', 'instruction_text'),
    'subscribe': ('subscribe_title', 'subscribe_text'),
    'register': ('register_title', 'register_text'),
    'deposit': ('deposit_title', 'deposit_text'),
    'access': ('access_title', 'access_text'),
    'platinum': ('platinum_title', 'platinum_text'),
    'admin': ('main_title', 'main_desc'),
    'langs': ('lang_title', 'lang_title'),
}

@router.callback_query(F.data.startswith("adm:content:screen:"))
async def cb_content_screen(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    _, _, _, lang, screen = c.data.split(":")
    title_key, text_key = SCREEN_MAP.get(screen, ('main_title', 'main_desc'))

    async with get_session() as session:
        res = await session.execute(select(ContentOverride).where(
            ContentOverride.lang == lang, ContentOverride.screen == screen
        ))
        ov = res.scalar_one_or_none()

    title = ov.title if ov and ov.title else title_key
    text = ov.text if ov and ov.text else text_key

    msg = (f"🧩 Контент — <b>{screen}</b> [{lang.upper()}]\n\n"
           f"<b>Заголовок:</b> <code>{h(title)}</code>\n<b>Текст:</b>\n<code>{h(text)[:900]}</code>")
    await c.message.edit_text(msg, reply_markup=kb_content_editor(lang, screen), parse_mode='HTML')
    await c.answer()


class ContentEditState(StatesGroup):
    waiting_text = State()
    waiting_photo = State()

@router.callback_query(F.data.startswith("adm:content:edit_text:"))
async def cb_content_edit_text(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        return
    _, _, _, lang, screen = c.data.split(":")
    await state.update_data(lang=lang, screen=screen)
    await c.message.edit_text(
        f"📝 Пришлите новый текст для [{lang.upper()} / {screen}].",
        reply_markup=kb_number_back(f"adm:content:screen:{lang}:{screen}")
    )
    await state.set_state(ContentEditState.waiting_text)
    await c.answer()

@router.message(ContentEditState.waiting_text)
async def on_content_text(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    data = await state.get_data()
    lang, screen = data["lang"], data["screen"]
    text = m.text or ""

    async with get_session() as session:
        res = await session.execute(select(ContentOverride).where(
            ContentOverride.lang == lang, ContentOverride.screen == screen
        ))
        ov = res.scalar_one_or_none()
        if not ov:
            ov = ContentOverride(lang=lang, screen=screen, text=text)
            session.add(ov)
        else:
            ov.text = text
        await session.commit()

    await m.answer("✅ Текст сохранён. /admin → Контент, чтобы посмотреть.")
    await state.clear()

@router.callback_query(F.data.startswith("adm:content:edit_photo:"))
async def cb_content_edit_photo(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        return
    _, _, _, lang, screen = c.data.split(":")
    await state.update_data(lang=lang, screen=screen)
    await c.message.edit_text(
        f"🖼️ Пришлите JPG изображение для [{lang.upper()} / {screen}].",
        reply_markup=kb_number_back(f"adm:content:screen:{lang}:{screen}")
    )
    await state.set_state(ContentEditState.waiting_photo)
    await c.answer()

@router.message(ContentEditState.waiting_photo, F.photo)
async def on_content_photo(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    data = await state.get_data()
    lang, screen = data["lang"], data["screen"]
    photo = m.photo[-1]
    path = Path("assets") / (("ru") if lang == "ru" else "en") / f"{screen}.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    await m.bot.download(photo, destination=path)
    await m.answer(f"✅ Картинка сохранена: {path}")
    await state.clear()


# --- params
class NumberState(StatesGroup):
    waiting_value = State()

@router.callback_query(F.data == "adm:param:locked:reg")
async def cb_param_locked_reg(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    await c.answer("Регистрация — обязательное условие и не может быть отключена.", show_alert=True)

@router.callback_query(F.data.startswith("adm:param:toggle:"))
async def cb_param_toggle(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    key = c.data.split(":")[-1]
    if key not in {"sub", "dep"}:
        # на всякий случай
        await cb_param_locked_reg(c)
        return

    map_keys = {"sub": "CHECK_SUBSCRIPTION", "dep": "CHECK_DEPOSIT"}
    cur = await get_value(map_keys[key], "1")
    new = not (str(cur).lower() in {"1", "true", "yes", "on"})
    await set_bool(map_keys[key], new)
    await cb_params(c)

@router.callback_query(F.data == "adm:params")
async def cb_params(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    fdep = await first_deposit_min()
    plat = await platinum_threshold()
    sub_on = await check_subscription_enabled()
    dep_on = await check_deposit_enabled()
    reg_on = await check_registration_enabled()  # просто для текста

    text = (
        "⚙️ <b>Параметры</b>\n\n"
        f"{'✅' if sub_on else '❌'} Проверка подписки   |  💵 Мин. деп: <b>${fdep:.0f}</b>\n"
        f"{'✅' if dep_on else '❌'} Проверка депозита   |  💎 Порог Platinum: <b>${plat:.0f}</b>\n"
        f"{'🔒' if reg_on else '🔓'} Регистрация"
    )
    await c.message.edit_text(text, reply_markup=kb_params(sub_on, dep_on), parse_mode='HTML')
    await c.answer()

@router.callback_query(F.data.startswith("adm:param:set:"))
async def cb_param_set(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        return
    what = c.data.split(":")[-1]
    await state.update_data(what=what)
    label = "минимальный депозит ($)" if what == "firstdep" else "порог Platinum ($)"
    await c.message.edit_text(f"Введите {label} числом:", reply_markup=kb_number_back("adm:params"))
    await state.set_state(NumberState.waiting_value)
    await c.answer()

@router.message(NumberState.waiting_value)
async def on_number_value(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    data = await state.get_data()
    what = data.get("what")
    try:
        val = float((m.text or "").strip().replace(",", "."))
        if val <= 0:
            raise ValueError
    except Exception:
        await m.answer("Нужно число больше 0. Попробуйте ещё раз.")
        return

    if what == "firstdep":
        await set_value("FIRST_DEPOSIT_MIN", str(val))
    else:
        await set_value("PLATINUM_THRESHOLD", str(val))
    await m.answer("✅ Сохранено. /admin → Параметры")
    await state.clear()


# --- broadcast (only group A)
class BroadcastState(StatesGroup):
    waiting_text = State()
    waiting_photo = State()

BCAST_SEGMENT = {}

@router.callback_query(F.data.startswith("adm:bcast:seg:"))
async def cb_bcast_seg(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    seg = c.data.split(":")[-1]
    BCAST_SEGMENT[c.from_user.id] = seg
    await c.answer("Сегмент выбран: " + seg, show_alert=False)

@router.callback_query(F.data == "adm:broadcast")
async def cb_broadcast(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    cur = BCAST_SEGMENT.get(c.from_user.id, "all")
    await c.message.edit_text(f"📣 Рассылка\nСегмент: {cur}", reply_markup=kb_broadcast())
    await c.answer()

@router.callback_query(F.data == "adm:bcast:text")
async def cb_bcast_text(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        return
    await c.message.edit_text("Пришлите текст рассылки:", reply_markup=kb_number_back("adm:broadcast"))
    await state.set_state(BroadcastState.waiting_text)
    await c.answer()

@router.message(BroadcastState.waiting_text)
async def on_bcast_text(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    await set_bcast_text(m.text or "")
    await m.answer("✅ Текст сохранён. /admin → Рассылка")
    await state.clear()

@router.callback_query(F.data == "adm:bcast:photo")
async def cb_bcast_photo(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        return
    await c.message.edit_text("Пришлите фото (как изображение):", reply_markup=kb_number_back("adm:broadcast"))
    await state.set_state(BroadcastState.waiting_photo)
    await c.answer()

@router.message(BroadcastState.waiting_photo, F.photo)
async def on_bcast_photo(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    file_id = m.photo[-1].file_id
    await set_bcast_photo(file_id)
    await m.answer("✅ Фото сохранено. /admin → Рассылка")
    await state.clear()

@router.callback_query(F.data == "adm:bcast:go")
async def cb_bcast_go(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    seg = BCAST_SEGMENT.get(c.from_user.id, "all")
    text = await bcast_text()
    photo = await bcast_photo()
    count_ok = 0
    count_err = 0

    async with get_session() as session:
        q = select(User).where(User.group_ab == 'A')  # B исключаем
        if seg == "reg":
            q = q.where(User.is_registered.is_(True))
        elif seg == "dep":
            q = q.where(User.has_deposit.is_(True))
        elif seg == "start":
            q = q.where(User.is_registered.is_(False), User.has_deposit.is_(False))
        res = await session.execute(q)
        users = res.scalars().all()

    for u in users:
        try:
            if photo:
                await c.bot.send_photo(u.telegram_id, photo=photo, caption=text or None)
            else:
                await c.bot.send_message(u.telegram_id, text or "(пусто)")
            count_ok += 1
        except Exception:
            count_err += 1
        await asyncio.sleep(0.03)

    await c.answer(f"Отправлено: {count_ok}, ошибок: {count_err}", show_alert=True)


# --- stats (only group A)
@router.callback_query(F.data == "adm:stats")
async def cb_stats(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    async with get_session() as session:
        total_a = await session.scalar(select(func.count(User.id)).where(User.group_ab == 'A'))
        subs_a  = await session.scalar(select(func.count(User.id)).where(User.group_ab == 'A', User.is_subscribed.is_(True)))
        regs_a  = await session.scalar(select(func.count(User.id)).where(User.group_ab == 'A', User.is_registered.is_(True)))
        deps_a  = await session.scalar(select(func.count(User.id)).where(User.group_ab == 'A', User.has_deposit.is_(True)))
        plats_a = await session.scalar(select(func.count(User.id)).where(User.group_ab == 'A', User.is_platinum.is_(True)))

    text = (
        "📊 <b>Статистика</b>\n\n"
        f"Юзеров: {total_a}\n"
        f"Подписались: {subs_a}\n"
        f"С регой: {regs_a}\n"
        f"С депозитом: {deps_a}\n"
        f"Платинум: {plats_a}"
    )
    await c.message.edit_text(text, reply_markup=kb_admin_menu(), parse_mode='HTML')
    await c.answer()
