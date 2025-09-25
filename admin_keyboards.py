from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def kb_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='👤 Пользователи', callback_data='adm:users:1')],
        [InlineKeyboardButton(text='✏️ Настройка постбэков', callback_data='adm:postbacks')],
        [InlineKeyboardButton(text='🧩 Контент', callback_data='adm:content') , InlineKeyboardButton(text='🔗 Ссылки', callback_data='adm:links')],
        [InlineKeyboardButton(text='⚙️ Параметры', callback_data='adm:params') , InlineKeyboardButton(text='📣 Рассылка', callback_data='adm:broadcast')],
        [InlineKeyboardButton(text='📊 Статистика', callback_data='adm:stats')],
    ])

def kb_back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🏠 В меню', callback_data='adm:menu')]])

def kb_users_list(items, page:int, has_prev:bool, has_next:bool) -> InlineKeyboardMarkup:
    rows = []
    for tg_id, label in items:
        rows.append([InlineKeyboardButton(text=label, callback_data=f'adm:user:{tg_id}')])
    nav = []
    if has_prev:
        nav.append(InlineKeyboardButton(text='◀️', callback_data=f'adm:users:{page-1}'))
    if has_next:
        nav.append(InlineKeyboardButton(text='▶️', callback_data=f'adm:users:{page+1}'))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text='🏠 В меню', callback_data='adm:menu')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_user_card(tg_id:int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Снять регистрацию ❌', callback_data=f'adm:user:clear_reg:{tg_id}')],
        [InlineKeyboardButton(text='Снять депозит ❌', callback_data=f'adm:user:clear_dep:{tg_id}')],
        [InlineKeyboardButton(text='Снять Platinum •', callback_data=f'adm:user:clear_platinum:{tg_id}')],
        [InlineKeyboardButton(text='⬅️ К списку', callback_data='adm:users:1'), InlineKeyboardButton(text='🏠 В меню', callback_data='adm:menu')],
    ])

def kb_links_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Изменить реф-ссылку', callback_data='adm:links:edit:refreg')],
        [InlineKeyboardButton(text='Изменить ссылку депоз.', callback_data='adm:links:edit:refdep')],
        [InlineKeyboardButton(text='Изменить канал (ID)', callback_data='adm:links:edit:channel')],
        [InlineKeyboardButton(text='Изменить Channel URL', callback_data='adm:links:edit:channel_url')],
        [InlineKeyboardButton(text='Изменить Support URL', callback_data='adm:links:edit:support')],
        [InlineKeyboardButton(text='🏠 В меню', callback_data='adm:menu')],
    ])

def kb_content_lang() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Русский', callback_data='adm:content:lang:ru'), InlineKeyboardButton(text='English', callback_data='adm:content:lang:en')],
        [InlineKeyboardButton(text='हिंदी', callback_data='adm:content:lang:hi'), InlineKeyboardButton(text='Español', callback_data='adm:content:lang:es')],
        [InlineKeyboardButton(text='🏠 В меню', callback_data='adm:menu')],
    ])

def kb_content_screens(lang:str) -> InlineKeyboardMarkup:
    btns = ['main','instruction','subscribe','register','deposit','access','platinum','admin','langs']
    rows = [[InlineKeyboardButton(text=name.capitalize() if name!='admin' else 'Экран админки', callback_data=f'adm:content:screen:{lang}:{name}') ] for name in btns]
    rows.append([InlineKeyboardButton(text='🏠 В меню', callback_data='adm:menu')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_content_editor(lang:str, screen:str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📝 Изменить текст', callback_data=f'adm:content:edit_text:{lang}:{screen}')],
        [InlineKeyboardButton(text='🖼️ Изменить картинку', callback_data=f'adm:content:edit_photo:{lang}:{screen}')],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data=f'adm:content:lang:{lang}')],
        [InlineKeyboardButton(text='🏠 В меню', callback_data='adm:menu')],
    ])

def kb_params(sub_on: bool, dep_on: bool, reg_on: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=('✅ ' if sub_on else '❌ ') + 'Проверка подписки',
                callback_data='adm:param:toggle:sub'
            ),
            InlineKeyboardButton(
                text=('✅ ' if dep_on else '❌ ') + 'Проверка депозита',
                callback_data='adm:param:toggle:dep'
            ),
        ],
        [
            InlineKeyboardButton(
                text=('🔒 ' if reg_on else '🔓 ') + 'Регистрация',
                callback_data='adm:param:toggle:reg'
            ),
            InlineKeyboardButton(text='💵 Мин. деп', callback_data='adm:param:set:firstdep'),
        ],
        [
            InlineKeyboardButton(text='💎 Порог Platinum', callback_data='adm:param:set:platinum'),
        ],
        [InlineKeyboardButton(text='🏠 В меню', callback_data='adm:menu')],
    ])


def kb_broadcast() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Всем', callback_data='adm:bcast:seg:all'), InlineKeyboardButton(text='С регистрацией', callback_data='adm:bcast:seg:reg')],
        [InlineKeyboardButton(text='С депозитом', callback_data='adm:bcast:seg:dep'), InlineKeyboardButton(text='Только /start', callback_data='adm:bcast:seg:start')],
        [InlineKeyboardButton(text='📝 Задать текст', callback_data='adm:bcast:text'), InlineKeyboardButton(text='🖼️ Прикрепить фото', callback_data='adm:bcast:photo')],
        [InlineKeyboardButton(text='🚀 Запустить', callback_data='adm:bcast:go')],
        [InlineKeyboardButton(text='🏠 В меню', callback_data='adm:menu')],
    ])

def kb_number_back(back_cb:str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='↩️ Отмена', callback_data=back_cb)]])
