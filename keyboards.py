from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from texts import t
from settings import settings

SUPPORT_DEEPLINK = f"tg://user?id={settings.ADMIN_ID}"

def kb_main(lang: str, is_platinum: bool, can_open: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(lang, 'btn_instruction'), callback_data='instructions')],
        [InlineKeyboardButton(text=t(lang, 'btn_support'), url=(settings.SUPPORT_URL or SUPPORT_DEEPLINK))],
        [InlineKeyboardButton(text=t(lang, 'btn_change_lang'), callback_data='lang')],
    ]
    if can_open:
        url = settings.MINI_APP_PLATINUM if is_platinum else settings.MINI_APP
        label = t(lang, 'btn_open_vip_miniapp') if is_platinum else t(lang, 'btn_open_miniapp')
        rows.append([InlineKeyboardButton(text=label, web_app=WebAppInfo(url=url))])
    else:
        rows.append([InlineKeyboardButton(text=t(lang, 'btn_get_signal'), callback_data='get_signal')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_instruction(lang: str, ref_reg_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, 'btn_register'), url=ref_reg_url)],
        [InlineKeyboardButton(text=t(lang, 'btn_menu'), callback_data='menu')],
    ])

def kb_lang() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Русский', callback_data='setlang:ru')],
        [InlineKeyboardButton(text='English', callback_data='setlang:en')],
        [InlineKeyboardButton(text='हिंदी', callback_data='setlang:hi')],
        [InlineKeyboardButton(text='Español', callback_data='setlang:es')],
        [InlineKeyboardButton(text='↩️', callback_data='menu')],
    ])

def kb_subscribe(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📣 Telegram', url=settings.CHANNEL_URL)],
        [InlineKeyboardButton(text=t(lang, 'btn_menu'), callback_data='menu')],
    ])

def kb_register(lang: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, 'btn_register'), url=url)],
        [InlineKeyboardButton(text=t(lang, 'btn_menu'), callback_data='menu')],
    ])

def kb_deposit(lang: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, 'btn_deposit'), url=url)],
        [InlineKeyboardButton(text=t(lang, 'btn_menu'), callback_data='menu')],
    ])

def kb_access(lang: str, vip: bool) -> InlineKeyboardMarkup:
    url = settings.MINI_APP_PLATINUM if vip else settings.MINI_APP
    label = t(lang, 'btn_open_vip_miniapp') if vip else t(lang, 'btn_open_miniapp')
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, web_app=WebAppInfo(url=url))],
        [InlineKeyboardButton(text=t(lang, 'btn_menu'), callback_data='menu')],
    ])
