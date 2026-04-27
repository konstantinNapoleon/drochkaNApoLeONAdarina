import asyncio
import random
import time
import datetime
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest

from items import GAME_ITEMS

# --- ОСНОВНЫЕ НАСТРОЙКИ ---
router = Router()
PASS_DURATION_DAYS = 14
QUEST_CHAT_ID = -100123456789  # ❗ ЗАМЕНИ НА ID ТВОЕГО ЧАТА! https://t.me/official_chat_droch
PHOTO_URL = "https://i.imgur.com/your_image.jpeg"  # ❗ ВСТАВЬ СЮДА ССЫЛКУ НА КАРТИНКУ ДЛЯ ПРОПУСКА

# --- СИМВОЛЫ И ВАЛЮТА ---
PEACH = "🍑"
FARMCOIN = "💰"
PREMIUM_COIN = "🪙"

# --- КОНФИГУРАЦИЯ УРОВНЕЙ ПРОПУСКА ---
# "xp": сколько 🍑 нужно для ДОСТИЖЕНИЯ этого уровня (от предыдущего)
# "rewards": список наград. (тип, id_предмета, количество). Типы: item, currency, premium
# "choice": для наград с выбором.

PASS_LEVELS = {
    1: {"xp": 50, "rewards": [("currency", FARMCOIN, 20000)]},
    2: {"xp": 75, "rewards": [("item", "🚚", 1)]},
    3: {"xp": 100, "rewards": [("item", "🍃", 2026)]},
    4: {"xp": 125, "rewards": [("currency", FARMCOIN, 32000)]},
    5: {"xp": 150, "rewards": [("currency", FARMCOIN, 10000), ("item", "📓", 1), ("item", "🎁", 1)]},
    6: {"xp": 175, "rewards": [("currency", FARMCOIN, 50000), ("item", "🔑", 1)]},
    7: {"xp": 200, "rewards": [("premium", PREMIUM_COIN, 10)]},
    8: {"xp": 225, "rewards": [("item", "🎁", 2), ("item", "🔰", 1)]},
    9: {"xp": 250, "rewards": [("currency", FARMCOIN, 100000), ("item", "💐", 1)]},
    10: {"xp": 300, "choice": [("item", "🍌", 1), ("item", "🍆", 1)]},
    # ... Добавь уровни с 11 по 20
    11: {"xp": 350, "rewards": [("currency", FARMCOIN, 150000)]},
    12: {"xp": 400, "rewards": [("item", "📦", 20)]},
    13: {"xp": 450, "rewards": [("premium", PREMIUM_COIN, 25)]},
    14: {"xp": 500, "rewards": [("item", "💫", 1)]},
    15: {"xp": 550, "rewards": [("item", "🎁", 5)]},
    16: {"xp": 600, "rewards": [("currency", FARMCOIN, 250000)]},
    17: {"xp": 650, "rewards": [("premium", PREMIUM_COIN, 50)]},
    18: {"xp": 700, "rewards": [("item", "🤖", 1)]},
    19: {"xp": 750, "rewards": [("currency", FARMCOIN, 500000)]},
    20: {"xp": 1000, "rewards": [("item", "💎", 1)]},
}

# --- КОНФИГУРАЦИЯ ЕЖЕДНЕВНЫХ ЗАДАНИЙ ---
# "id": уникальный идентификатор
# "text": описание
# "target": сколько раз нужно сделать действие
# "reward": сколько 🍑 дается в награду
# "type": для кастомной логики отслеживания

DAILY_QUESTS = {
    "msg_50": {"id": "msg_50", "text": f"Написать 50 сообщений в чат", "target": 50, "reward": 200, "type": "messages"},
    "droch_rand": {"id": "droch_rand", "text": "Подрочить {} раз", "target": random.choice([100, 250, 400]),
                   "reward": 60, "type": "droch"},
    "trade_1": {"id": "trade_1", "text": "Произвести 1 успешный трейд", "target": 1, "reward": 40, "type": "trade"},
    "give_1": {"id": "give_1", "text": "Передать 1 предмет другому игроку", "target": 1, "reward": 20, "type": "give"},
    "pizda_1": {"id": "pizda_1", "text": "Получить пизды от создателя", "target": 1, "reward": 150, "type": "pizda"},
    "spray_30": {"id": "spray_30", "text": "Использовать 30 спреев", "target": 30, "reward": 30, "type": "spray"},
}


# --- CALLBACK ДАННЫЕ ДЛЯ КНОПОК ---

class PassMenu(CallbackData, prefix="pass"):
    action: str  # "view_levels", "view_quests", "bonus", "buy_ultra", "info", "back_main"
    level: int = 1


class LevelChoice(CallbackData, prefix="pass_choice"):
    level: int
    item_id: str
    item_count: int


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_pass_end_date(user_data):
    end_ts = user_data.get("pass", {}).get("end_date")
    if not end_ts:
        return "Никогда"
    days_left = (end_ts - time.time()) / 86400
    if days_left <= 0:
        return "Завершён"
    return f"{int(days_left)} дней"


def get_today_str():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def ensure_user_pass_data(user_data: dict):
    """Инициализирует/обновляет данные пропуска для пользователя."""
    if "pass" not in user_data:
        user_data["pass"] = {
            "level": 1,
            "xp": 0,
            "pass_type": "Обычный",
            "end_date": time.time() + (PASS_DURATION_DAYS * 86400),
            "claimed_levels": [],
            "daily_bonus_claimed": None,
            "quests": {}
        }

    today = get_today_str()
    if user_data["pass"]["quests"].get("date") != today:
        # Генерируем новые квесты
        quest_ids = random.sample(list(DAILY_QUESTS.keys()), 2)
        user_data["pass"]["quests"] = {
            "date": today,
            "tasks": {qid: {"progress": 0, "completed": False} for qid in quest_ids}
        }
    return user_data


# --- ГЛАВНОЕ МЕНЮ ПРОПУСКА (/pass) ---

@router.message(Command("pass"))
async def cmd_pass_menu(message: types.Message, get_user):
    user = await get_user(message.from_user.id, message.from_user.username)
    user = ensure_user_pass_data(user)

    pass_data = user["pass"]
    text = (
        f"<b>ДРОЧ ПАСС</b>\n\n"
        f"<b>Твой этап:</b> {pass_data['level']}\n"
        f"<b>Пропуск:</b> {pass_data['pass_type']}\n"
        f"<b>Дней до окончания:</b> {get_pass_end_date(user)}"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="Этапы", callback_data=PassMenu(action="view_levels", level=pass_data['level']))
    builder.button(text="Задания", callback_data=PassMenu(action="view_quests"))
    builder.button(text="Бонус", callback_data=PassMenu(action="bonus"))
    builder.button(text="Купить Ультра пропуск", callback_data=PassMenu(action="buy_ultra"))
    builder.button(text="Информация", callback_data=PassMenu(action="info"))
    builder.adjust(1, 2, 1, 1)

    await message.answer_photo(photo=PHOTO_URL, caption=text, reply_markup=builder.as_markup())


# --- ОБРАБОТЧИК НАЖАТИЙ НА КНОПКИ ГЛАВНОГО МЕНЮ ---

@router.callback_query(PassMenu.filter())
async def handle_pass_menu_callbacks(query: types.CallbackQuery, callback_data: PassMenu, get_user, save_db):
    action = callback_data.action
    user = await get_user(query.from_user.id, query.from_user.username)
    user = ensure_user_pass_data(user)
    pass_data = user["pass"]

    # --- НАВИГАЦИЯ ---
    if action == "back_main":
        await query.message.delete()
        await cmd_pass_menu(query.message, get_user)
        return

    # --- ИНФОРМАЦИЯ ---
    if action == "info":
        await query.answer(
            "Дроч Пасс - это сезонный ивент, где ты выполняешь задания, получаешь 🍑 и забираешь награды!",
            show_alert=True)
        return

    # --- ПОКУПКА УЛЬТРА ---
    if action == "buy_ultra":
        # ❗ Здесь будет твоя логика покупки. Например, проверка баланса 🪙
        await query.answer("Покупка Ультра пропуска пока не реализована.", show_alert=True)
        return

    # --- ЕЖЕДНЕВНЫЙ БОНУС ---
    if action == "bonus":
        today = get_today_str()
        if pass_data.get("daily_bonus_claimed") == today:
            await query.answer("Ты уже забирал бонус сегодня. Приходи завтра!", show_alert=True)
        else:
            pass_data["xp"] += 50
            pass_data["daily_bonus_claimed"] = today
            await save_db(query.from_user.id, user)
            await query.answer(f"✅ Ты получил +50 {PEACH}!", show_alert=True)
        return

    # --- ПРОСМОТР ЗАДАНИЙ ---
    if action == "view_quests":
        text = "<b>Текущие ежедневные задания:</b>\n\n"
        tasks = pass_data["quests"]["tasks"]

        for i, (quest_id, data) in enumerate(tasks.items()):
            quest_info = DAILY_QUESTS[quest_id]
            status = "✅" if data["completed"] else "❌"

            # Динамическая подстановка цели для рандомных квестов
            q_text = quest_info['text']
            if '{}' in q_text:
                q_text = q_text.format(quest_info['target'])

            text += f"<b>[{i + 1}]</b> {q_text} ({data['progress']}/{quest_info['target']}) {status}\n"

        # ❗ Логика таймера до обновления (упрощенная)
        text += "\nОбновление через ~24 часа."

        builder = InlineKeyboardBuilder()
        builder.button(text="‹ Назад", callback_data=PassMenu(action="back_main"))

        await query.message.edit_caption(caption=text, reply_markup=builder.as_markup())

    # --- ПРОСМОТР ЭТАПОВ ---
    if action == "view_levels":
        level_to_show = callback_data.level
        level_data = PASS_LEVELS.get(level_to_show)

        if not level_data:
            await query.answer("Это был последний уровень!", show_alert=False)
            return

        # --- Проверка и повышение уровня ---
        # Эта логика должна быть здесь, чтобы обновлять статус "на лету"
        while pass_data["level"] in PASS_LEVELS and pass_data["xp"] >= PASS_LEVELS[pass_data["level"]]["xp"]:
            xp_needed = PASS_LEVELS[pass_data["level"]]["xp"]
            pass_data["xp"] -= xp_needed
            pass_data["level"] += 1
        await save_db(query.from_user.id, user)
        # ---

        header = f"📦 <b>Боевой Пропуск | Уровень {level_to_show}</b>\n\n<b>Награда:</b>\n"
        rewards_text = ""

        # Обычные награды
        if "rewards" in level_data:
            for r_type, r_id, r_count in level_data["rewards"]:
                name = GAME_ITEMS.get(r_id, {}).get("name", "Неизвестно")
                rewards_text += f"{r_id} {name} ({r_count} шт.)\n"

        # Награды на выбор
        if "choice" in level_data:
            rewards_text += "🎁 *Награда на выбор:*\n"
            for r_type, r_id, r_count in level_data["choice"]:
                name = GAME_ITEMS.get(r_id, {}).get("name", "Неизвестно")
                rewards_text += f" L {r_id} {name} ({r_count} шт.)\n"

        # --- Прогресс бар ---
        current_level_xp_needed = PASS_LEVELS.get(pass_data['level'], {}).get("xp", 1)
        prev_level_xp_needed = PASS_LEVELS.get(pass_data['level'] - 1, {}).get("xp", 0)

        progress_text = f"\n<b>Прогресс Ур. {pass_data['level'] - 1}</b> ▱▱▱▱▱▱▱▱▱▱ {pass_data['xp']}/{current_level_xp_needed} {PEACH}"

        # --- Статус и кнопки ---
        status = ""
        builder = InlineKeyboardBuilder()

        # Кнопки навигации
        nav_buttons = []
        if level_to_show > 1:
            nav_buttons.append(types.InlineKeyboardButton(text="⬅️", callback_data=PassMenu(action="view_levels",
                                                                                            level=level_to_show - 1).pack()))
        if level_to_show < len(PASS_LEVELS):
            nav_buttons.append(types.InlineKeyboardButton(text="➡️", callback_data=PassMenu(action="view_levels",
                                                                                            level=level_to_show + 1).pack()))
        builder.row(*nav_buttons)

        # Кнопка "Забрать"
        if pass_data["level"] > level_to_show:
            if level_to_show in pass_data["claimed_levels"]:
                status = "Статус: [✅ получено]"
            else:
                status = "Статус: [🔘 ожидает сбор]"
                if "choice" in level_data:
                    # Если есть выбор, добавляем кнопки выбора
                    choice_buttons = []
                    for r_type, r_id, r_count in level_data["choice"]:
                        choice_buttons.append(types.InlineKeyboardButton(text=f"Выбрать {r_id}",
                                                                         callback_data=LevelChoice(level=level_to_show,
                                                                                                   item_id=r_id,
                                                                                                   item_count=r_count).pack()))
                    builder.row(*choice_buttons)
                else:
                    # Обычная кнопка "Забрать"
                    builder.button(text="Забрать", callback_data=PassMenu(action="claim", level=level_to_show))
        elif pass_data["level"] == level_to_show:
            status = f"Статус: [в процессе...]"
        else:
            status = f"Статус: [не достигнуто]"

        builder.button(text="‹ Назад в меню", callback_data=PassMenu(action="back_main"))

        final_text = f"{header}{rewards_text}—————————\n{progress_text}\n\n{status}"

        # Используем suppress для игнорирования ошибки, если сообщение не изменилось
        with suppress(TelegramBadRequest):
            await query.message.edit_caption(caption=final_text, reply_markup=builder.as_markup())


# --- ОБРАБОТЧИК КНОПКИ "ЗАБРАТЬ" (ДЛЯ ОБЫЧНЫХ НАГРАД) ---
@router.callback_query(PassMenu.filter(F.action == "claim"))
async def claim_pass_reward(query: types.CallbackQuery, callback_data: PassMenu, get_user, save_db):
    user = await get_user(query.from_user.id, query.from_user.username)
    # Перепроверяем данные на всякий случай
    user = ensure_user_pass_data(user)
    pass_data = user["pass"]
    level_to_claim = callback_data.level

    if level_to_claim >= pass_data["level"]:
        return await query.answer("Ты еще не достиг этого уровня!", show_alert=True)
    if level_to_claim in pass_data["claimed_levels"]:
        return await query.answer("Награда уже была получена.", show_alert=True)

    level_data = PASS_LEVELS[level_to_claim]
    inv = user.get("inventory", {})
    if not isinstance(inv, dict): inv = {}  # На всякий случай

    for r_type, r_id, r_count in level_data["rewards"]:
        # Добавляем предмет с тем же ключом (r_id), который используется в inventar.py
        inv[r_id] = inv.get(r_id, 0) + r_count

    pass_data["claimed_levels"].append(level_to_claim)
    user["inventory"] = inv
    await save_db(query.from_user.id, user)

    await query.answer("✅ Награда успешно получена!", show_alert=True)
    # Обновляем сообщение, чтобы убрать кнопку
    await handle_pass_menu_callbacks(query, PassMenu(action="view_levels", level=level_to_claim), get_user, save_db)


# --- ОБРАБОТЧИК КНОПКИ ВЫБОРА НАГРАДЫ (уровень 10) ---
@router.callback_query(LevelChoice.filter())
async def claim_pass_choice_reward(query: types.CallbackQuery, callback_data: LevelChoice, get_user, save_db):
    user = await get_user(query.from_user.id, query.from_user.username)
    user = ensure_user_pass_data(user)
    pass_data = user["pass"]
    level_to_claim = callback_data.level

    if level_to_claim >= pass_data["level"]:
        return await query.answer("Ты еще не достиг этого уровня!", show_alert=True)
    if level_to_claim in pass_data["claimed_levels"]:
        return await query.answer("Награда уже была получена.", show_alert=True)

    inv = user.get("inventory", {})
    if not isinstance(inv, dict): inv = {}

    # Добавляем выбранный предмет
    inv[callback_data.item_id] = inv.get(callback_data.item_id, 0) + callback_data.item_count

    pass_data["claimed_levels"].append(level_to_claim)
    user["inventory"] = inv
    await save_db(query.from_user.id, user)

    await query.answer(f"✅ Ты выбрал и получил {callback_data.item_id}!", show_alert=True)
    # Обновляем сообщение, чтобы убрать кнопки выбора
    await handle_pass_menu_callbacks(query, PassMenu(action="view_levels", level=level_to_claim), get_user, save_db)


# --- ВНЕШНЯЯ ФУНКЦИЯ ДЛЯ ДОБАВЛЕНИЯ ПРОГРЕССА В КВЕСТЫ ---
async def add_quest_progress(user_id: int, quest_type: str, amount: int, get_user, save_db, bot: Bot):
    user = await get_user(user_id, None)
    user = ensure_user_pass_data(user)

    tasks = user["pass"]["quests"].get("tasks", {})
    updated = False

    for quest_id, data in tasks.items():
        if data["completed"]:
            continue

        quest_info = DAILY_QUESTS[quest_id]
        if quest_info["type"] == quest_type:
            data["progress"] = min(data["progress"] + amount, quest_info["target"])
            if data["progress"] >= quest_info["target"]:
                data["completed"] = True
                user["pass"]["xp"] += quest_info["reward"]
                await bot.send_message(user_id,
                                       f"✅ Задание выполнено: *{quest_info['text'].format(quest_info['target'])}*\n"
                                       f"Ты получил +{quest_info['reward']} {PEACH}!")
            updated = True

    if updated:
        await save_db(user_id, user)