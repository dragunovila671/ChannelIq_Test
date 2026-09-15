import os
import threading
import sqlite3
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==================================================
# 🔑 ТОКЕН БОТА
# ==================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Ошибка: переменная BOT_TOKEN не задана")
# =========================
# 📊 СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ
# =========================

DB_FILE = "channeliq_stats.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            first_seen TEXT,
            last_seen TEXT
        )
    """)

    conn.commit()
    conn.close()


def register_user(user):
    if not user:
        return

    now = datetime.now().isoformat()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user.id,)
    )

    if cursor.fetchone():
        cursor.execute("""
            UPDATE users
            SET username = ?, first_name = ?, last_seen = ?
            WHERE user_id = ?
        """, (
            user.username,
            user.first_name,
            now,
            user.id
        ))
    else:
        cursor.execute("""
            INSERT INTO users
            (user_id, username, first_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user.id,
            user.username,
            user.first_name,
            now,
            now
        ))

    conn.commit()
    conn.close()


def get_stats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    today = datetime.now().date().isoformat()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE date(first_seen) = ?
    """, (today,))

    today_users = cursor.fetchone()[0]

    week_ago = (datetime.now() - timedelta(days=7)).isoformat()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE first_seen >= ?
    """, (week_ago,))

    week_users = cursor.fetchone()[0]

    day_ago = (datetime.now() - timedelta(days=1)).isoformat()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE last_seen >= ?
    """, (day_ago,))

    active_24h = cursor.fetchone()[0]

    conn.close()

    return total, today_users, week_users, active_24h
    # =========================
# 📊 КОМАНДА /STATS
# =========================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not user or user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ У тебя нет доступа к этой команде."
        )
        return

    total, today, week, active = get_stats()

    await update.message.reply_text(
        f"📊 ChannelIQ — статистика\n\n"
        f"👥 Всего пользователей: {total}\n"
        f"🆕 Новых сегодня: {today}\n"
        f"📅 Новых за 7 дней: {week}\n"
        f"🟢 Активных за 24 часа: {active}"
    )

# =========================
# 🏠 ГЛАВНОЕ МЕНЮ
# =========================

MAIN_MENU = [
    ["📊 Анализ", "💡 Идеи"],
    ["📝 Скрипт", "📅 План"],
    ["🏷️ Название", "🖼️ Превью"],
    ["👀 Первые просмотры", "🔥 Популярные ниши"],
    ["📈 Развитие канала"],
    ["⚙️ Помощь", "ℹ️ О боте"]
]


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ChannelIQ is running!")

    def log_message(self, format, *args):
        pass


def run_web_server():
    port = int(os.environ.get("PORT", 10000))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(f"🌐 Web server запущен на порту {port}")

    server.serve_forever()





def main_keyboard():
    return ReplyKeyboardMarkup(
        MAIN_MENU,
        resize_keyboard=True
    )


# =========================
# /START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)

    await update.message.reply_text(
        "🤖 ChannelIQ\n\n"
        "Твой помощник для развития YouTube-канала.\n\n"
        "Выбери нужную функцию 👇",
        reply_markup=main_keyboard()
    )

# =========================
# 📊 АНАЛИЗ
# =========================

async def analysis_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🔗 Анализ канала"],
        ["📊 Анализ видео"],
        ["💡 Что улучшить"],
        ["🎯 Как увеличить просмотры"],
        ["⬅️ Главное меню"]
    ]

    await update.message.reply_text(
        "📊 АНАЛИЗ\n\n"
        "Выбери, что хочешь проанализировать:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def analyze_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔗 АНАЛИЗ КАНАЛА\n\n"
        "Для полноценного анализа в будущем ты сможешь отправить "
        "ссылку на YouTube-канал.\n\n"
        "ChannelIQ сможет анализировать:\n"
        "• количество подписчиков\n"
        "• просмотры\n"
        "• частоту публикаций\n"
        "• популярные видео\n"
        "• тематику канала\n"
        "• лучшие форматы\n\n"
        "🚀 Функция будет дорабатываться."
    )


async def analyze_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 АНАЛИЗ ВИДЕО\n\n"
        "В будущем отправь ссылку на видео, и ChannelIQ сможет "
        "оценить:\n\n"
        "👀 просмотры\n"
        "👍 лайки\n"
        "💬 комментарии\n"
        "📝 название\n"
        "🖼️ превью\n"
        "⏱️ удержание\n\n"
        "И даст рекомендации по улучшению."
    )


async def what_improve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 ЧТО УЛУЧШИТЬ\n\n"
        "Главные вещи, которые стоит проверять:\n\n"
        "1️⃣ Название должно вызывать интерес.\n"
        "2️⃣ Превью должно быть понятным с первого взгляда.\n"
        "3️⃣ Первые секунды видео должны удерживать зрителя.\n"
        "4️⃣ Не затягивай вступление.\n"
        "5️⃣ Делай контент регулярно.\n"
        "6️⃣ Анализируй ролики, которые получили больше всего просмотров."
    )


async def increase_views(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 КАК УВЕЛИЧИТЬ ПРОСМОТРЫ\n\n"
        "🔥 Делай сильный первый кадр.\n"
        "🔥 Используй понятные названия.\n"
        "🔥 Тестируй разные темы.\n"
        "🔥 Создавай Shorts.\n"
        "🔥 Следи за удержанием аудитории.\n"
        "🔥 Не удаляй видео сразу после слабого старта.\n"
        "🔥 Анализируй успешные ролики своей ниши."
    )


# =========================
# 💡 ИДЕИ
# =========================

async def ideas_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🎬 Идея для Shorts"],
        ["🎥 Идея для видео"],
        ["🔥 10 идей"],
        ["🎯 Идея под мою нишу"],
        ["⬅️ Главное меню"]
    ]

    await update.message.reply_text(
        "💡 ИДЕИ ДЛЯ КОНТЕНТА\n\n"
        "Выбери вариант:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def shorts_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 ИДЕЯ ДЛЯ SHORTS\n\n"
        "🔥 Идея: «3 ошибки, которые уничтожают твои просмотры»\n\n"
        "Структура:\n"
        "1. Сильный вопрос в первые 2 секунды.\n"
        "2. Покажи ошибку.\n"
        "3. Объясни решение.\n"
        "4. Заверши коротким призывом подписаться."
    )


async def video_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎥 ИДЕЯ ДЛЯ ВИДЕО\n\n"
        "«Я попробовал развить YouTube-канал с нуля за 30 дней»\n\n"
        "Можно показать весь путь:\n"
        "📅 День 1 → создание канала\n"
        "📹 Первые видео\n"
        "📊 Первые просмотры\n"
        "📈 Результаты\n"
        "🏆 Итог эксперимента"
    )


async def ten_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 10 ИДЕЙ ДЛЯ КОНТЕНТА\n\n"
        "1. 5 ошибок новичков\n"
        "2. Я попробовал сделать...\n"
        "3. Топ-10 лучших способов...\n"
        "4. Что будет, если...\n"
        "5. Проверяю популярный совет\n"
        "6. До и после\n"
        "7. Самый дешёвый vs самый дорогой\n"
        "8. 30 дней эксперимента\n"
        "9. Мифы о моей нише\n"
        "10. Что я хотел бы знать до начала канала"
    )


async def niche_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 ИДЕЯ ПОД ТВОЮ НИШУ\n\n"
        "Напиши мне свою нишу следующим сообщением.\n\n"
        "Например:\n"
        "⚽ футбол\n"
        "🎮 игры\n"
        "🚗 автомобили\n"
        "💻 технологии\n"
        "🎬 монтаж"
    )


# =========================
# 📝 СКРИПТ
# =========================

async def script_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🎬 Скрипт для Shorts"],
        ["🎥 Скрипт для видео"],
        ["🔥 Вирусный скрипт"],
        ["⚽ Футбольный скрипт"],
        ["🎮 Игровой скрипт"],
        ["⬅️ Главное меню"]
    ]

    await update.message.reply_text(
        "📝 СКРИПТ\n\n"
        "Выбери тип сценария:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def shorts_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 СКРИПТ ДЛЯ SHORTS\n\n"
        "🎯 Хук:\n"
        "«Ты точно делаешь это неправильно!»\n\n"
        "📌 Основная часть:\n"
        "Покажи проблему и быстро объясни решение.\n\n"
        "🔥 Финал:\n"
        "«Попробуй это в следующем видео и сравни результат.»"
    )


async def video_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎥 СКРИПТ ДЛЯ ВИДЕО\n\n"
        "1️⃣ Хук — заинтересуй зрителя.\n"
        "2️⃣ Объясни, что произойдёт в видео.\n"
        "3️⃣ Основная часть.\n"
        "4️⃣ Неожиданный момент или результат.\n"
        "5️⃣ Вывод.\n"
        "6️⃣ Призыв подписаться."
    )


async def viral_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 ВИРУСНЫЙ СКРИПТ\n\n"
        "«Я решил проверить то, что делают почти все блогеры...»\n\n"
        "Дальше:\n"
        "➡️ Покажи эксперимент.\n"
        "➡️ Создай проблему.\n"
        "➡️ Покажи неожиданный результат.\n"
        "➡️ Сделай финальный вывод."
    )


async def football_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ ФУТБОЛЬНЫЙ СКРИПТ\n\n"
        "«Я решил проверить, насколько хорошо я умею бить пенальти...»\n\n"
        "🎬 Первый удар\n"
        "🔥 Сложность\n"
        "😱 Неожиданный момент\n"
        "🏆 Финальная попытка"
    )


async def gaming_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 ИГРОВОЙ СКРИПТ\n\n"
        "«Я попробовал пройти эту игру, используя только...»\n\n"
        "1. Правила челленджа\n"
        "2. Первая попытка\n"
        "3. Неожиданная проблема\n"
        "4. Самый сложный момент\n"
        "5. Финальная попытка\n"
        "6. Результат"
    )


# =========================
# 📅 ПЛАН
# =========================

async def plan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📅 План на неделю"],
        ["📆 План на месяц"],
        ["🎯 План для новичка"],
        ["📱 План Shorts"],
        ["⬅️ Главное меню"]
    ]

    await update.message.reply_text(
        "📅 КОНТЕНТ-ПЛАН\n\n"
        "Выбери нужный вариант:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def weekly_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📅 ПЛАН НА НЕДЕЛЮ\n\n"
        "Пн — 🎬 Shorts\n"
        "Вт — 💡 Подготовка идеи\n"
        "Ср — 🎥 Основное видео\n"
        "Чт — 🎬 Shorts\n"
        "Пт — 📊 Анализ статистики\n"
        "Сб — 🎬 Shorts\n"
        "Вс — 💡 Подготовка контента"
    )


async def monthly_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📆 ПЛАН НА МЕСЯЦ\n\n"
        "🎬 12–20 Shorts\n"
        "🎥 4–8 длинных видео\n"
        "📊 4 анализа статистики\n"
        "💡 Постоянный поиск новых тем\n"
        "🖼️ Тестирование разных превью\n"
        "🏷️ Тестирование названий"
    )


async def beginner_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 ПЛАН ДЛЯ НОВИЧКА\n\n"
        "1️⃣ Выбери одну нишу.\n"
        "2️⃣ Оформи канал.\n"
        "3️⃣ Подготовь 10 идей.\n"
        "4️⃣ Выпусти первые 5–10 роликов.\n"
        "5️⃣ Посмотри статистику.\n"
        "6️⃣ Повтори лучшие форматы.\n"
        "7️⃣ Постепенно улучшай качество."
    )


async def shorts_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📱 ПЛАН SHORTS\n\n"
        "Понедельник — 1 Shorts\n"
        "Среда — 1 Shorts\n"
        "Пятница — 1 Shorts\n"
        "Суббота — 1 Shorts\n"
        "Воскресенье — анализ\n\n"
        "Главное — стабильность."
    )


# =========================
# 🏷️ НАЗВАНИЕ
# =========================

async def title_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🔥 Кликабельное название"],
        ["🎬 Название для Shorts"],
        ["🧠 10 вариантов"],
        ["🎯 Название под нишу"],
        ["⬅️ Главное меню"]
    ]

    await update.message.reply_text(
        "🏷️ НАЗВАНИЯ\n\n"
        "Выбери вариант:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def clickable_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 КЛИКАБЕЛЬНОЕ НАЗВАНИЕ\n\n"
        "Пример:\n"
        "«Я НЕ ОЖИДАЛ такого результата…»\n\n"
        "Или:\n"
        "«Я проверил это — и пожалел»"
    )


async def shorts_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 НАЗВАНИЯ ДЛЯ SHORTS\n\n"
        "• Ты точно этого не знал 😳\n"
        "• Вот почему у тебя мало просмотров\n"
        "• Я попробовал это впервые\n"
        "• Это реально работает?!\n"
        "• Не повторяй эту ошибку!"
    )


async def ten_titles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 10 ВАРИАНТОВ\n\n"
        "1. Я попробовал это впервые\n"
        "2. Никто не ожидал такого результата\n"
        "3. Что произойдёт, если...\n"
        "4. Я проверил популярный миф\n"
        "5. Это оказалось сложнее, чем я думал\n"
        "6. Почему все делают это неправильно\n"
        "7. Самый неожиданный результат\n"
        "8. Я потратил на это 30 дней\n"
        "9. Стоит ли это вообще делать?\n"
        "10. Вот что произошло..."
    )


async def niche_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 НАЗВАНИЕ ПОД НИШУ\n\n"
        "Напиши свою нишу или тему видео.\n\n"
        "Например:\n"
        "«футбол»\n"
        "«Minecraft»\n"
        "«автомобили»\n"
        "«монтаж»"
    )


# =========================
# 🖼️ ПРЕВЬЮ
# =========================

async def thumbnail_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["💡 Идея для превью"],
        ["🔥 Кликабельное превью"],
        ["🎨 Стиль превью"],
        ["❌ Ошибки превью"],
        ["⬅️ Главное меню"]
    ]

    await update.message.reply_text(
        "🖼️ ИДЕИ ДЛЯ ПРЕВЬЮ\n\n"
        "Выбери функцию:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def thumbnail_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 ИДЕЯ ДЛЯ ПРЕВЬЮ\n\n"
        "Используй:\n\n"
        "😱 Яркую эмоцию\n"
        "👆 Один главный объект\n"
        "🔴 Короткий текст из 2–4 слов\n"
        "🎯 Контраст между объектами\n\n"
        "Пример текста:\n"
        "«Я НЕ ОЖИДАЛ!»"
    )


async def clickable_thumbnail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 КЛИКАБЕЛЬНОЕ ПРЕВЬЮ\n\n"
        "Формула:\n"
        "Лицо/объект + эмоция + интрига.\n\n"
        "❌ Не помещай много текста.\n"
        "❌ Не делай 10 разных объектов.\n"
        "✅ Один главный смысл."
    )


async def thumbnail_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎨 СТИЛЬ ПРЕВЬЮ\n\n"
        "Попробуй:\n"
        "• крупный главный объект\n"
        "• размытый фон\n"
        "• короткий текст\n"
        "• сильный контраст\n"
        "• стрелки только если они реально нужны"
    )


async def thumbnail_mistakes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ ОШИБКИ ПРЕВЬЮ\n\n"
        "1. Слишком много текста.\n"
        "2. Слишком много объектов.\n"
        "3. Непонятно, о чём видео.\n"
        "4. Маленький главный объект.\n"
        "5. Превью не вызывает интерес."
    )


# =========================
# 👀 ПЕРВЫЕ ПРОСМОТРЫ
# =========================

async def first_views_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🎯 Первые 100 просмотров"],
        ["🔥 Первые 1000 просмотров"],
        ["🚀 Как попасть в рекомендации"],
        ["📱 Продвижение Shorts"],
        ["❌ Ошибки новичков"],
        ["⬅️ Главное меню"]
    ]

    await update.message.reply_text(
        "👀 ПЕРВЫЕ ПРОСМОТРЫ\n\n"
        "Выбери тему:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def first_100(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 ПЕРВЫЕ 100 ПРОСМОТРОВ\n\n"
        "1️⃣ Сделай несколько Shorts.\n"
        "2️⃣ Используй сильный первый кадр.\n"
        "3️⃣ Тестируй разные темы.\n"
        "4️⃣ Не удаляй ролик слишком быстро.\n"
        "5️⃣ Анализируй, что работает."
    )


async def first_1000(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 ПЕРВЫЕ 1000 ПРОСМОТРОВ\n\n"
        "Для роста попробуй несколько разных форматов.\n\n"
        "Если один ролик получил значительно больше просмотров — "
        "сделай ещё несколько видео на похожую тему."
    )


async def recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 КАК ПОПАСТЬ В РЕКОМЕНДАЦИИ\n\n"
        "Никто не может гарантировать попадание в рекомендации.\n\n"
        "Но повышают шансы:\n"
        "🔥 хороший CTR\n"
        "⏱️ высокое удержание\n"
        "💬 реакции зрителей\n"
        "🎯 правильная тема\n"
        "📱 хороший формат Shorts"
    )


async def promote_shorts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📱 ПРОДВИЖЕНИЕ SHORTS\n\n"
        "• Делай короткое вступление.\n"
        "• Не начинай с долгого приветствия.\n"
        "• Первые секунды — самые важные.\n"
        "• Тестируй разные хуки.\n"
        "• Используй понятные заголовки.\n"
        "• Делай серию роликов на одну тему."
    )


async def beginner_mistakes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ ОШИБКИ НОВИЧКОВ\n\n"
        "1. Постоянно менять нишу.\n"
        "2. Копировать чужой контент.\n"
        "3. Сдаваться после нескольких роликов.\n"
        "4. Игнорировать аналитику.\n"
        "5. Делать слишком длинные вступления."
    )


# =========================
# 🔥 ПОПУЛЯРНЫЕ НИШИ
# =========================

async def niches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 ПОПУЛЯРНЫЕ НИШИ YOUTUBE\n\n"
        "🎮 Gaming\n"
        "⚽ Спорт\n"
        "🚗 Автомобили\n"
        "💻 Технологии\n"
        "🤖 AI\n"
        "🎬 Развлекательный контент\n"
        "📚 Обучение\n"
        "💰 Финансы\n"
        "🏋️ Спорт и фитнес\n"
        "🎥 Влоги\n\n"
        "⚠️ Популярная ниша не гарантирует просмотры. "
        "Важнее найти тему, которую ты сможешь регулярно развивать."
    )


# =========================
# 📈 РАЗВИТИЕ КАНАЛА
# =========================

async def development_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🌱 Канал с 0 подписчиков"],
        ["🚀 Первые 100 подписчиков"],
        ["🔥 1000 подписчиков"],
        ["💰 Путь к монетизации"],
        ["🏆 Долгосрочный рост"],
        ["⬅️ Главное меню"]
    ]

    await update.message.reply_text(
        "📈 ПЛАН РАЗВИТИЯ КАНАЛА\n\n"
        "Выбери этап:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def zero_subscribers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌱 КАНАЛ С 0 ПОДПИСЧИКОВ\n\n"
        "1. Определи нишу.\n"
        "2. Оформи канал.\n"
        "3. Подготовь 10–20 идей.\n"
        "4. Начни регулярно публиковать.\n"
        "5. Анализируй каждую неделю."
    )


async def hundred_subscribers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 ПЕРВЫЕ 100 ПОДПИСЧИКОВ\n\n"
        "Главная задача — найти формат, который работает.\n\n"
        "Создавай серии похожих роликов и постепенно улучшай "
        "названия, первые секунды и монтаж."
    )


async def thousand_subscribers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 1000 ПОДПИСЧИКОВ\n\n"
        "На этом этапе особенно важно:\n"
        "📊 смотреть аналитику\n"
        "🎯 понимать свою аудиторию\n"
        "🔥 повторять успешные форматы\n"
        "🎬 улучшать качество контента\n"
        "📅 сохранять регулярность"
    )


async def monetization(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 ПУТЬ К МОНЕТИЗАЦИИ\n\n"
        "Требования YouTube могут меняться, поэтому перед подачей "
        "заявки всегда проверяй актуальные условия в YouTube Studio.\n\n"
        "Главное сейчас — развивать аудиторию и создавать "
        "оригинальный контент."
    )


async def long_growth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏆 ДОЛГОСРОЧНЫЙ РОСТ\n\n"
        "📌 Ниша\n"
        "📌 Регулярность\n"
        "📌 Качество\n"
        "📌 Аналитика\n"
        "📌 Эксперименты\n"
        "📌 Общение с аудиторией\n\n"
        "Не оценивай канал только по одному видео."
    )


# =========================
# ⚙️ ПОМОЩЬ
# =========================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ ПОМОЩЬ\n\n"
        "ChannelIQ помогает создавать и развивать YouTube-канал.\n\n"
        "Основные функции:\n"
        "📊 Анализ\n"
        "💡 Идеи\n"
        "📝 Скрипты\n"
        "📅 Планы\n"
        "🏷️ Названия\n"
        "🖼️ Превью\n"
        "👀 Первые просмотры\n"
        "🔥 Популярные ниши\n"
        "📈 Развитие канала\n\n"
        "Команда /start — открыть главное меню."
    )


# =========================
# ℹ️ О БОТЕ
# =========================

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ О CHANNELIQ\n\n"
        "ChannelIQ — помощник для YouTube-креаторов.\n\n"
        "Платформа: YouTube\n\n"
        "🚀 Новые возможности будут добавляться в следующих обновлениях."
    )


# =========================
# ⬅️ ГЛАВНОЕ МЕНЮ
# =========================

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 Главное меню",
        reply_markup=main_keyboard()
    )


# =========================
# 🔘 ОБРАБОТКА КНОПОК
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    # Главное меню
    if text == "📊 Анализ":
        await analysis_menu(update, context)

    elif text == "💡 Идеи":
        await ideas_menu(update, context)

    elif text == "📝 Скрипт":
        await script_menu(update, context)

    elif text == "📅 План":
        await plan_menu(update, context)

    elif text == "🏷️ Название":
        await title_menu(update, context)

    elif text == "🖼️ Превью":
        await thumbnail_menu(update, context)

    elif text == "👀 Первые просмотры":
        await first_views_menu(update, context)

    elif text == "🔥 Популярные ниши":
        await niches(update, context)

    elif text == "📈 Развитие канала":
        await development_menu(update, context)

    elif text == "⚙️ Помощь":
        await help_command(update, context)

    elif text == "ℹ️ О боте":
        await about(update, context)

    # Анализ
    elif text == "🔗 Анализ канала":
        await analyze_channel(update, context)

    elif text == "📊 Анализ видео":
        await analyze_video(update, context)

    elif text == "💡 Что улучшить":
        await what_improve(update, context)

    elif text == "🎯 Как увеличить просмотры":
        await increase_views(update, context)

    # Идеи
    elif text == "🎬 Идея для Shorts":
        await shorts_idea(update, context)

    elif text == "🎥 Идея для видео":
        await video_idea(update, context)

    elif text == "🔥 10 идей":
        await ten_ideas(update, context)

    elif text == "🎯 Идея под мою нишу":
        await niche_idea(update, context)

    # Скрипты
    elif text == "🎬 Скрипт для Shorts":
        await shorts_script(update, context)

    elif text == "🎥 Скрипт для видео":
        await video_script(update, context)

    elif text == "🔥 Вирусный скрипт":
        await viral_script(update, context)

    elif text == "⚽ Футбольный скрипт":
        await football_script(update, context)

    elif text == "🎮 Игровой скрипт":
        await gaming_script(update, context)

    # План
    elif text == "📅 План на неделю":
        await weekly_plan(update, context)

    elif text == "📆 План на месяц":
        await monthly_plan(update, context)

    elif text == "🎯 План для новичка":
        await beginner_plan(update, context)

    elif text == "📱 План Shorts":
        await shorts_plan(update, context)

    # Названия
    elif text == "🔥 Кликабельное название":
        await clickable_title(update, context)

    elif text == "🎬 Название для Shorts":
        await shorts_title(update, context)

    elif text == "🧠 10 вариантов":
        await ten_titles(update, context)

    elif text == "🎯 Название под нишу":
        await niche_title(update, context)

    # Превью
    elif text == "💡 Идея для превью":
        await thumbnail_idea(update, context)

    elif text == "🔥 Кликабельное превью":
        await clickable_thumbnail(update, context)

    elif text == "🎨 Стиль превью":
        await thumbnail_style(update, context)

    elif text == "❌ Ошибки превью":
        await thumbnail_mistakes(update, context)

    # Первые просмотры
    elif text == "🎯 Первые 100 просмотров":
        await first_100(update, context)

    elif text == "🔥 Первые 1000 просмотров":
        await first_1000(update, context)

    elif text == "🚀 Как попасть в рекомендации":
        await recommendations(update, context)

    elif text == "📱 Продвижение Shorts":
        await promote_shorts(update, context)

    elif text == "❌ Ошибки новичков":
        await beginner_mistakes(update, context)

    # Развитие канала
    elif text == "🌱 Канал с 0 подписчиков":
        await zero_subscribers(update, context)

    elif text == "🚀 Первые 100 подписчиков":
        await hundred_subscribers(update, context)

    elif text == "🔥 1000 подписчиков":
        await thousand_subscribers(update, context)

    elif text == "💰 Путь к монетизации":
        await monetization(update, context)

    elif text == "🏆 Долгосрочный рост":
        await long_growth(update, context)

    # Назад
    elif text == "⬅️ Главное меню":
        await back_to_main(update, context)
 

   
# =========================
# 🚀 ЗАПУСК
# =========================

def main():
    init_db()

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("stats", stats))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            buttons
        )
    )

    print("🤖 ChannelIQ запущен!")

    app.run_polling()


if __name__ == "__main__":
    main()
