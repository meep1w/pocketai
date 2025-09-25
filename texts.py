from typing import Dict

# Локализованные строки интерфейса
T: Dict[str, Dict[str, str]] = {
    # Главный экран
    'main_title': {
        'ru': 'Главное меню', 'en': 'Main Menu', 'hi': 'मुख्य मेनू', 'es': 'Menú principal'
    },
    'main_desc': {
        'ru': 'Выберите действие ниже.', 'en': 'Choose an action below.',
        'hi': 'नीचे से कोई कार्रवाई चुनें।', 'es': 'Elige una acción abajo.'
    },

    # Кнопки главного экрана
    'btn_instruction': {
        'ru': '📘 Инструкция', 'en': '📘 Instructions', 'hi': '📘 निर्देश', 'es': '📘 Instrucciones'
    },
    'btn_support': {
        'ru': '🆘 Поддержка', 'en': '🆘 Support', 'hi': '🆘 सहायता', 'es': '🆘 Soporte'
    },
    'btn_change_lang': {
        'ru': '🌐 Сменить язык', 'en': '🌐 Change language', 'hi': '🌐 भाषा बदलें', 'es': '🌐 Cambiar idioma'
    },
    'btn_get_signal': {
        'ru': '🚀 Получить сигнал', 'en': '🚀 Get signal', 'hi': '🚀 सिग्नल प्राप्त करें', 'es': '🚀 Obtener señal'
    },
    'btn_open_miniapp': {
        'ru': '🔓 Открыть мини-апп', 'en': '🔓 Open mini-app',
        'hi': '🔓 मिनी-ऐप खोलें', 'es': '🔓 Abrir mini-app'
    },
    'btn_open_vip_miniapp': {
        'ru': '👑 Открыть VIP мини-апп', 'en': '👑 Open VIP mini-app',
        'hi': '👑 VIP मिनी-ऐप खोलें', 'es': '👑 Abrir mini-app VIP'
    },

    # Инструкция
    'instruction_title': {
        'ru': 'Как начать', 'en': 'How to start', 'hi': 'कैसे शुरू करें', 'es': 'Cómo empezar'
    },
    'instruction_text': {
        'ru': '1) Зарегистрируйтесь у брокера через бота.\n'
              '2) Дождитесь автоматической проверки регистрации.\n'
              '3) Внесите первый депозит (≥ $10).\n'
              '4) После проверки откройте мини-апп.',
        'en': '1) Register with the broker via the bot.\n'
              '2) Wait for automatic registration check.\n'
              '3) Make your first deposit (≥ $10).\n'
              '4) After verification, open the mini-app.',
        'hi': '1) बॉट से ब्रोक़र पर पंजीकरण करें।\n'
              '2) स्वत: जाँच का इंतज़ार करें।\n'
              '3) पहला जमा करें (≥ $10).\n'
              '4) जाँच के बाद मिनी-ऐप खोलें.',
        'es': '1) Regístrate con el bróker mediante el bot.\n'
              '2) Espera la verificación automática.\n'
              '3) Haz tu primer depósito (≥ $10).\n'
              '4) Tras verificar, abre la mini-app.'
    },
    'btn_register': {
        'ru': '📝 Зарегистрироваться', 'en': '📝 Register',
        'hi': '📝 पंजीकरण', 'es': '📝 Registrarse'
    },
    'already_registered': {
        'ru': 'Вы уже зарегистрированы ✅',
        'en': 'You are already registered ✅',
        'hi': 'आप पहले से पंजीकृत हैं ✅',
        'es': 'Ya estás registrado ✅'
    },

    # Экраны шагов
    'lang_title': {
        'ru': 'Выберите язык', 'en': 'Choose language', 'hi': 'भाषा चुनें', 'es': 'Elige idioma'
    },

    'subscribe_title': {
        'ru': 'Шаг 1 — Подписка', 'en': 'Step 1 — Subscribe',
        'hi': 'चरण 1 — सदस्यता', 'es': 'Paso 1 — Suscribirse'
    },
    'subscribe_text': {
        'ru': 'Подпишитесь на наш канал, затем вернитесь в бота.',
        'en': 'Subscribe to our channel, then return to the bot.',
        'hi': 'हमारे चैनल को सब्सक्राइब करें, फिर बॉट पर लौटें।',
        'es': 'Suscríbete a nuestro canal y vuelve al bot.'
    },
    'btn_ive_subscribed': {
        'ru': '🔄 Я подписался', 'en': "🔄 I've subscribed",
        'hi': '🔄 मैंने सदस्यता ले ली', 'es': '🔄 Ya me suscribí'
    },
    'sub_confirmed': {
        'ru': 'Подписка подтверждена ✅',
        'en': 'Subscription confirmed ✅',
        'hi': 'सदस्यता की पुष्टि हो गई ✅',
        'es': 'Suscripción confirmada ✅'
    },
    'sub_not_yet': {
        'ru': 'Пока не вижу подписку. Проверьте, что вы вступили в канал и попробуйте ещё раз.',
        'en': "I don't see the subscription yet. Please join the channel and try again.",
        'hi': 'अभी सदस्यता नहीं दिख रही। कृपया चैनल जॉइन करें और फिर से प्रयास करें।',
        'es': 'Aún no veo la suscripción. Únete al canal e inténtalo de nuevo.'
    },

    'register_title': {
        'ru': 'Шаг 2 — Регистрация', 'en': 'Step 2 — Registration',
        'hi': 'चरण 2 — पंजीकरण', 'es': 'Paso 2 — Registro'
    },
    'register_text': {
        'ru': 'Зарегистрируйтесь у брокера через кнопку ниже.',
        'en': 'Register with the broker via the button below.',
        'hi': 'नीचे दिए बटन से पंजीकरण करें।',
        'es': 'Regístrate con el bróker usando el botón.'
    },

    'deposit_title': {
        'ru': 'Шаг 3 — Депозит', 'en': 'Step 3 — Deposit',
        'hi': 'चरण 3 — जमा', 'es': 'Paso 3 — Depósito'
    },
    'deposit_text': {
        'ru': 'Внесите первый депозит через кнопку ниже (минимум $10).',
        'en': 'Make your first deposit via the button below (minimum $10).',
        'hi': 'पहली जमा राशि नीचे दिए बटन से करें (न्यूनतम $10)।',
        'es': 'Realiza tu primer depósito con el botón (mínimo $10).'
    },

    'access_title': {
        'ru': 'Доступ открыт', 'en': 'Access granted',
        'hi': 'प्रवेश खुला', 'es': 'Acceso concedido'
    },
    'access_text': {
        'ru': 'Вы выполнили все шаги. Откройте мини-апп.',
        'en': 'All steps are complete. Open the mini-app.',
        'hi': 'सभी चरण पूरे। मिनी-ऐप खोलें।',
        'es': 'Todos los pasos completos. Abre la mini-app.'
    },

    # Депозит/Platinum
    'btn_deposit': {
        'ru': '💳 Внести депозит', 'en': '💳 Deposit',
        'hi': '💳 जमा करें', 'es': '💳 Depositar'
    },

    'platinum_title': {
        'ru': 'Поздравляем! Платинум', 'en': 'Congratulations! Platinum',
        'hi': 'बधाई! प्लेटिनम', 'es': '¡Felicidades! Platino'
    },
    'platinum_text': {
        'ru': 'Ваш общий депозит достиг порога. Доступна VIP мини-апп.',
        'en': 'Your total deposits reached the threshold. VIP mini-app is available.',
        'hi': 'आपकी कुल जमा राशि सीमा तक पहुंच गई है। VIP मिनी-ऐप उपलब्ध है।',
        'es': 'Tus depósitos alcanzaron el umbral. Mini-app VIP disponible.'
    },

    # Навигация
    'btn_menu': {
        'ru': '↩️ В главное меню', 'en': '↩️ Main menu',
        'hi': '↩️ मुख्य मेनू', 'es': '↩️ Menú principal'
    },
}


def t(lang: str, key: str) -> str:
    """Безопасное извлечение перевода с фоллбэком на EN/ключ."""
    d = T.get(key) or {}
    return d.get(lang) or d.get('en') or key
