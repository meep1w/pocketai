from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from texts import t
from settings import settings

# deep-link поддержки (если SUPPORT_URL не задан)
SUPPORT_DEEPLINK = settings.SUPPORT_URL or f"tg://user?id={settings.PRIMARY_ADMIN}"


def kb_main(lang: str, is_platinum: bool, can_open: bool) -> InlineKeyboardMarkup:
    """
    Ряд 1:  📘 Инструкция
    Ряд 2:  🆘 Поддержка | 🌐 Сменить язык
    Ряд 3:  🚀 Получить сигнал  (или открыть мини-апп, если доступ уже открыт)
    """
    rows = [
        [InlineKeyboardButton(text=t(lang, "btn_instruction"), callback_data="instructions")],
        [
            InlineKeyboardButton(text=t(lang, "btn_support"), url=(settings.SUPPORT_URL or SUPPORT_DEEPLINK)),
            InlineKeyboardButton(text=t(lang, "btn_change_lang"), callback_data="lang"),
        ],
    ]

    if can_open:
        url = settings.MINI_APP_PLATINUM if is_platinum else settings.MINI_APP
        label = t(lang, "btn_open_vip_miniapp") if is_platinum else t(lang, "btn_open_miniapp")
        rows.append([InlineKeyboardButton(text=label, web_app=WebAppInfo(url=url))])
    else:
        rows.append([InlineKeyboardButton(text=t(lang, "btn_get_signal"), callback_data="get_signal")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_instruction(lang: str) -> InlineKeyboardMarkup:
    """
    Кнопка регистрации теперь callback (btn_register),
    чтобы можно было показать алерт «уже зарегистрированы».
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_register"), callback_data="btn_register")],
        [InlineKeyboardButton(text=t(lang, "btn_menu"),     callback_data="menu")],
    ])


def kb_lang() -> InlineKeyboardMarkup:
    """
    Две строки по два языка с флагами + «В меню».
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский",  callback_data="setlang:ru"),
            InlineKeyboardButton(text="🇬🇧 English",  callback_data="setlang:en"),
        ],
        [
            InlineKeyboardButton(text="🇮🇳 हिन्दी",   callback_data="setlang:hi"),
            InlineKeyboardButton(text="🇪🇸 Español", callback_data="setlang:es"),
        ],
        [InlineKeyboardButton(text="↩️ В меню", callback_data="menu")],
    ])


def kb_subscribe(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📣 Telegram', url=settings.CHANNEL_URL)],
        [InlineKeyboardButton(text=t(lang, 'btn_ive_subscribed'), callback_data='check_sub')],
        [InlineKeyboardButton(text=t(lang, 'btn_menu'), callback_data='menu')],
    ])



def kb_register(lang: str, url: str) -> InlineKeyboardMarkup:
    """
    Если где-то в потоке всё ещё нужна именно URL-кнопка регистрации,
    оставляем утилиту (не используется на экране «Инструкция»).
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_register"), url=url)],
        [InlineKeyboardButton(text=t(lang, "btn_menu"), callback_data="menu")],
    ])


def kb_deposit(lang: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_deposit"), url=url)],
        [InlineKeyboardButton(text=t(lang, "btn_menu"), callback_data="menu")],
    ])


def kb_access(lang: str, vip: bool) -> InlineKeyboardMarkup:
    url = settings.MINI_APP_PLATINUM if vip else settings.MINI_APP
    label = t(lang, "btn_open_vip_miniapp") if vip else t(lang, "btn_open_miniapp")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, web_app=WebAppInfo(url=url))],
        [InlineKeyboardButton(text=t(lang, "btn_menu"), callback_data="menu")],
    ])
