import time
import html
import random
from datetime import datetime, timezone, timedelta
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импорты
from handlers.etel import get_user_buffs
from handlers.ivent import get_random_event
from items import GAME_ITEMS  # Импорт базы предметов для получения инфо о дропе
from ivent.pass_tasks import progress_task


router = Router()

MSK_TZ = timezone(timedelta(hours=3))
FARMCOIN_EMOJI = "💰"

# Цены и данные предметов для событий
EVENT_ITEMS_INFO = {
    "mom": {"emoji": "🛌", "name": "Одеяло", "price": 15},
    "erection": {"emoji": "💉", "name": "Шприц", "price": 7},
    "sadness": {"emoji": "📕", "name": "журнал FamHub", "price": 7}
}

RANKS = {
    1: "🙋 Школьник",
    20: "🚬 Студент",
    50: "🔫 Начинающий",
    100: "👏 Прогрессирующий",
    200: "⭐️ Профессионал",
    300: "🥇 Авторитет",
    500: "🌟 Властелин дрочки",
    750: "⭐️⭐️ Легенда",
    1000: "🌟🌟 Охотник за семенем",
    3000: "⭐️⭐️⭐️ Генерал дрочки",
    5000: "🌟🌟🌟 Бесконечный дрочер",
    10000: "🏆 Гранд-повелитель",
    50000: "💎 Демиург Онанизма",
    100000: "👑 Хранитель семени"
}

import time


def update_stress_decay(user):
    """Снижает стресс на 1 ед. каждые 15 секунд."""
    current_time = int(time.time())

    # Если времени спада еще нет, задаем его прямо сейчас и ждем 15 сек.
    if user.get("last_stress_decay_time") is None:
        user["last_stress_decay_time"] = current_time
        return user

    last_decay = user["last_stress_decay_time"]
    stress = user.get("stress", 0)

    if stress > 0:
        elapsed = current_time - last_decay
        if elapsed >= 15:
            decay_amount = int(elapsed // 15)
            user["stress"] = max(0, stress - decay_amount)
            # Сдвигаем время на количество прошедших 15-секундных интервалов
            user["last_stress_decay_time"] = last_decay + (decay_amount * 15)
    else:
        # Если стресса нет, просто обновляем таймер, чтобы он не копил "долг"
        user["last_stress_decay_time"] = current_time

    return user


def get_current_rank(droch_count: int) -> str:
    """Определяет актуальный ранг на основе общего количества дрочек."""
    current_rank = "👶 Новичок"
    for count in sorted(RANKS.keys()):
        if droch_count >= count:
            current_rank = RANKS[count]
        else:
            break
    return current_rank


def get_current_date_str():
    return datetime.now(MSK_TZ).strftime("%Y-%m-%d")


def get_real_total(user) -> int:
    """Считает честное общее кол-во дрочек для исправления рангов у старичков."""
    chats_data = user.get("chats_data", {})
    total_from_chats = sum(c.get("masturbations_count", 0) for c in chats_data.values())
    return max(user.get("total_droch_count", 0), total_from_chats)


def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        if isinstance(inv, list):
            new_inv = {}
            for item in inv:
                new_inv[item] = new_inv.get(item, 0) + 1
            user["inventory"] = new_inv
        else:
            user["inventory"] = {}
    return user["inventory"]


def get_spray_markup(spray_count: int, user_id: int):
    if spray_count <= 0:
        return None
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"💦 Применить спрей ({spray_count})",
        callback_data=f"use_spray_callback:{user_id}"
    )
    return builder.as_markup()


# --- Обновленная функция для кнопок (ПРИМЕНЕНИЕ / ПОКУПКА / ТОРГОВЛЯ) ---
def get_event_fix_markup(reason: str, inv: dict, user_id: int):
    builder = InlineKeyboardBuilder()
    info = EVENT_ITEMS_INFO.get(reason)

    if not info: return None

    emoji = info["emoji"]
    name = info["name"]
    price = info["price"]

    # Если предмет есть — кнопка применения
    if inv.get(emoji, 0) > 0:
        builder.button(text=f"{emoji} Применить {name} ({inv[emoji]})", callback_data=f"fix_event:{emoji}:{user_id}")
    else:
        # Если предмета нет — кнопка купить и кнопка торговли
        builder.button(text=f"{emoji} Купить {name} ({price}{FARMCOIN_EMOJI})",
                       callback_data=f"buy_step1:{reason}:{user_id}")
        builder.button(text="🤝 Найти в торговле", url="https://t.me/Tradedroch")

    if len(builder.as_markup().inline_keyboard) > 0:
        builder.adjust(1)
        return builder.as_markup()
    return None


# --- НОВЫЕ ФУНКЦИИ ДЛЯ ПРОФИЛЯ ---

def get_me_markup(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Закрыть", callback_data=f"inv_close_{user_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_me_text(user, chat_id: str, full_name: str):
    # ПРИМЕНЯЕМ ПАССИВНЫЙ СПАД СТРЕССА
    update_stress_decay(user)

    chats_data = user.get("chats_data", {})
    inv = ensure_inv_dict(user)

    # Получаем баффы (стамина и удача)
    buffs = get_user_buffs(user)

    # Вычисляем проценты бонусов (множитель 1.15 = 15%)
    stamina_bonus = int((buffs["stamina_multiplier"] - 1.0) * 100)
    luck_bonus = int((buffs["luck_multiplier"] - 1.0) * 100)

    total_global = get_real_total(user)
    rank = get_current_rank(total_global)
    farmcoin_count = inv.get(FARMCOIN_EMOJI, 0)
    stress = user.get("stress", 0)

    # Синхронизация с ТОПом
    total_in_groups = sum(c.get("masturbations_count", 0) for cid, c in chats_data.items() if int(cid) < 0)
    daily_droch = user.get("daily_stats", {}).get(get_current_date_str(), 0)
    chat_droch = chats_data.get(chat_id, {}).get("masturbations_count", 0)

    return (
        f"👤 <b>Профиль:</b> {html.escape(full_name)}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎖 <b>Позывной:</b> {rank}\n\n"
        f"{FARMCOIN_EMOJI} ФармКоин: <b>{farmcoin_count:,}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"💪 <b>Характеристики:</b>\n"
        f"├ 🧤 Выносливость: <b>{stamina_bonus}%</b>\n"
        f"└ 🍀 Удача: <b>{luck_bonus}%</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"📊 <b>Статистика дрочки:</b>\n"
        f"├ 🧘 Стресс: <b>{stress}%</b>\n"
        f"├ 🎲 В этом чате: <b>{chat_droch}</b>\n"
        f"├ 🔥 За сегодня: <b>{daily_droch}</b> \n"
        f"└ 🏆 Всего в группах (ТОП): <b>{total_in_groups}</b> \n"
    )


@router.message(Command("me"))
async def cmd_me(message: types.Message, get_user):
    user = await get_user(message.from_user.id, message.from_user.username)
    text = get_me_text(user, str(message.chat.id), message.from_user.full_name)
    await message.reply(text, parse_mode="HTML", reply_markup=get_me_markup(message.from_user.id))


@router.callback_query(F.data.startswith("open_me:"))
async def callback_open_me(callback: types.CallbackQuery, get_user):
    owner_id = int(callback.data.split(":")[1])
    if callback.from_user.id != owner_id:
        return await callback.answer("Это не твой профиль!", show_alert=True)
    user = await get_user(callback.from_user.id, callback.from_user.username)
    text = get_me_text(user, str(callback.message.chat.id), callback.from_user.full_name)
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_me_markup(owner_id))
    except Exception:
        await callback.answer()


# --- ЛОГИКА ДРОЧКИ ---

async def process_droch(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    # ПРИМЕНЯЕМ ПАССИВНЫЙ СПАД СТРЕССА
    update_stress_decay(user)

    chat_id = str(message.chat.id)
    inv = ensure_inv_dict(user)
    spray_count = inv.get("💦", 0)
    current_time = time.time()

    # --- ПРОВЕРКА СТРЕССА ---
    if user.get("stress", 0) >= 100:
        return await message.reply("Твой стресс слишком высок, поэтому твой дружок не встаёт")

    # --- ПРОВЕРКА ПОЯСА ИЛИ СОБЫТИЙ (РАЗДЕЛЕННАЯ) ---
    belt_expire = user.get("belt_expire_time", 0)
    if current_time < belt_expire:
        reason = user.get("lock_reason", "belt")
        remaining = int(belt_expire - current_time)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60

        if reason == "mom":
            text = f"Ты всё ещё прячешься от мамки! 🙈\nСможешь продолжить через <b>{hours}ч. {minutes}мин.</b>"
        elif reason == "erection":
            text = f"Твой хер всё ещё в коме... 🥀\nОсталось ждать <b>{hours}ч. {minutes}мин.</b>"
        elif reason == "sadness":
            text = f"Ты всё ещё грустишь потому что не нашел порнуху... 😭\nНастроение вернется через <b>{hours}ч. {minutes}мин.</b>"
        else:
            text = f"На тебе пояс верности. 🔒 Ты не можешь дрочить ещё <b>{hours}ч. {minutes}мин.</b>!"

        # Генерируем кнопку, если есть предмет
        markup = get_event_fix_markup(reason, inv, message.from_user.id)
        return await message.reply(text, parse_mode="HTML", reply_markup=markup)

    buffs = get_user_buffs(user)
    BASE_COOLDOWN = 1800
    current_cooldown = int(BASE_COOLDOWN / buffs["stamina_multiplier"])

    if "chats_data" not in user:
        user["chats_data"] = {}
    if chat_id not in user["chats_data"]:
        user["chats_data"][chat_id] = {"masturbations_count": 0, "last_droch_time": 0, "chat_name": ""}

    chat_stats = user["chats_data"][chat_id]
    chat_stats["chat_name"] = message.chat.title or "Личные сообщения"
    last_time = chat_stats.get("last_droch_time", 0)
    time_passed = current_time - last_time

    if time_passed < current_cooldown:
        remaining_seconds = int(current_cooldown - time_passed)
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        buff_text = ""
        if buffs["stamina_multiplier"] > 1.0:
            percent = int((buffs["stamina_multiplier"] - 1.0) * 100)
            buff_text = f"\n<i>(Твое КД снижено на {percent}% благодаря баффам!)</i>"
        return await message.reply(
            f"Ты недавно дрочил! 🤕 \nПриходи через <b>{minutes} мин. {seconds} сек.</b>{buff_text}",
            reply_markup=get_spray_markup(spray_count, message.from_user.id),
            parse_mode="HTML"
        )

    # --- НОВАЯ ПРОВЕРКА: СЛУЧАЙНЫЕ СОБЫТИЯ (5% ШАНС) ---
    event = get_random_event()
    if event:
        user["belt_expire_time"] = current_time + event["seconds"]
        user["lock_reason"] = event["id"]  # Запоминаем причину (mom или erection)
        await save_db(message.from_user.id, user)

        # Сразу предлагаем кнопку исправления при выпадении события
        markup = get_event_fix_markup(event["id"], inv, message.from_user.id)
        return await message.reply(event["text"], parse_mode="HTML", reply_markup=markup)

    chat_stats["masturbations_count"] += 1

    # --- НОВОЕ: ШАНС 5% НА ВЫПАДЕНИЕ ПРЕДМЕТА ---
    drop_info_text = ""
    if random.random() < 0.05:
        drop_pool = ["💜", "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟪", "📕", "💦", "🔑", "💉"]
        selected_item = random.choice(drop_pool)
        amount = random.randint(1, 7)

        # Добавляем в инвентарь
        inv[selected_item] = inv.get(selected_item, 0) + amount

        # Получаем данные из GAME_ITEMS
        item_data = GAME_ITEMS.get(selected_item, {})
        it_name = item_data.get("name", "Неизвестный предмет")
        it_desc = item_data.get("description", "Без описания")

        drop_info_text = f"\n\nТы получил {selected_item} <b>{it_name}</b>: {it_desc} (<b>{amount}</b>)"

    # Исправленное обновление ранга
    old_rank = user.get("rank", "👶 Новичок")
    total_droch = get_real_total(user) + 1  # Используем функцию исправления
    user["total_droch_count"] = total_droch
    current_calculated_rank = get_current_rank(total_droch)

    if current_calculated_rank != old_rank:
        user["rank"] = current_calculated_rank
        await message.answer(f"🎊 <b>Новое звание!</b>\nТеперь ты: <b>{current_calculated_rank}</b>!", parse_mode="HTML")

    dispenser_active = user.get("spray_dispenser_active", False)
    dispenser_triggered = False
    if dispenser_active and inv.get("🚰", 0) > 0 and inv.get("💦", 0) > 0:
        inv["💦"] -= 1
        chat_stats["last_droch_time"] = 0
        dispenser_triggered = True
    else:
        chat_stats["last_droch_time"] = current_time

    if "daily_stats" not in user:
        user["daily_stats"] = {}
    current_date = get_current_date_str()
    user["daily_stats"][current_date] = user["daily_stats"].get(current_date, 0) + 1

    # --- ПРИБАВЛЕНИЕ СТРЕССА ---
    user["stress"] = min(100, user.get("stress", 0) + 3)

    if "achievements" not in user or not isinstance(user["achievements"], list):
        user["achievements"] = []
    if "first_droch" not in user["achievements"]:
        user["achievements"].append("first_droch")
        await message.answer("🎊 НОВОЕ ДОСТИЖЕНИЕ: ✊ Первая дрочка!")

    await save_db(message.from_user.id, user)

    if dispenser_triggered:
        reply_text = f"Ты успешно вздрочнул! 😼\nНа твоем счету <b>{chat_stats['masturbations_count']}</b> вздрочки.{drop_info_text}\n\n🚰 Дозатор спрея сработал и теперь можешь дрочить ещё раз!"
        await message.reply(reply_text, parse_mode="HTML")
        await progress_task(message.from_user.id, "mast_20", 1)
    else:
        reply_text = f"Ты успешно вздрочнул! 😼\nНа твоем счету <b>{chat_stats['masturbations_count']}</b> вздрочки.{drop_info_text}"
        await message.reply(reply_text, reply_markup=get_spray_markup(inv.get("💦", 0), message.from_user.id),
                            parse_mode="HTML")
        await progress_task(message.from_user.id, "mast_20", 1)


# --- ЭТАП 1: ПОКУПКА ПРЕДМЕТА "НА ЛЕТУ" ---
@router.callback_query(F.data.startswith("buy_step1:"))
async def callback_buy_step1(callback: types.CallbackQuery, get_user, save_db):
    _, reason, owner_id = callback.data.split(":")
    if callback.from_user.id != int(owner_id):
        return await callback.answer("Это не твоё предложение!", show_alert=True)

    user = await get_user(callback.from_user.id, callback.from_user.username)
    inv = ensure_inv_dict(user)
    info = EVENT_ITEMS_INFO.get(reason)
    if not info: return await callback.answer("Ошибка данных.")

    price = info["price"]
    if inv.get(FARMCOIN_EMOJI, 0) < price:
        return await callback.answer(f"Недостаточно ФармКоинов! Нужно {price}{FARMCOIN_EMOJI}", show_alert=True)

    # Списываем монеты и ДОБАВЛЯЕМ предмет в инвентарь
    inv[FARMCOIN_EMOJI] -= price
    inv[info["emoji"]] = inv.get(info["emoji"], 0) + 1
    await save_db(callback.from_user.id, user)

    # Меняем сообщение на текст о покупке с кнопкой "Применить"
    builder = InlineKeyboardBuilder()
    builder.button(text=f"{info['emoji']} Применить {info['name']}",
                   callback_data=f"fix_event:{info['emoji']}:{owner_id}")

    await callback.message.edit_text(
        f"Ты купил 1 {info['emoji']} за {price} {FARMCOIN_EMOJI}! 🐺",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer("Успешно куплено!")


# --- ЭТАП 2: ОБРАБОТЧИК КНОПОК ПРИМЕНЕНИЯ (С ЗАЩИТОЙ) ---
@router.callback_query(F.data.startswith("fix_event:"))
async def callback_fix_event(callback: types.CallbackQuery, get_user, save_db):
    _, item_emoji, owner_id = callback.data.split(":")
    if callback.from_user.id != int(owner_id):
        return await callback.answer("Это не твой предмет!", show_alert=True)

    user = await get_user(callback.from_user.id, callback.from_user.username)
    current_time = time.time()

    # ПРОВЕРКА: Если блокировка уже снята
    if current_time >= user.get("belt_expire_time", 0):
        already_ok_responses = {
            "💉": "Твой член здоров. 👍 Шприц не нужен.",
            "🛌": "Мамки нет рядом. 👍 Одеяло не нужно.",
            "📕": "Ты больше не грустишь. 👍 Журнал не нужен."
        }
        try:
            await callback.message.edit_text(already_ok_responses.get(item_emoji, "Всё уже в порядке! ✨"),
                                             parse_mode="HTML")
        except Exception:
            pass
        return await callback.answer("Ты уже здоров!")

    inv = ensure_inv_dict(user)
    chat_id = str(callback.message.chat.id)

    if inv.get(item_emoji, 0) <= 0:
        return await callback.answer("Предмет закончился в инвентаре!")

    responses = {
        "💉": "Тестостерон резко прилил к херу и ты можешь дрочить! 💪",
        "🛌": "Тссс... Ты спрятался от мамки и можешь дрочить! 👌",
        "📕": "Ты полистал журнал FamHub и грусть как рукой сняло! 📕✨"
    }

    # Тратим предмет и снимаем блокировку
    inv[item_emoji] -= 1
    user["belt_expire_time"] = 0
    user["lock_reason"] = None
    if "chats_data" in user and chat_id in user["chats_data"]:
        user["chats_data"][chat_id]["last_droch_time"] = 0

    await save_db(callback.from_user.id, user)
    await callback.message.edit_text(responses.get(item_emoji, "Эффект снят!"), parse_mode="HTML")
    await callback.answer("Готово! Можешь дрочить.")


@router.callback_query(F.data.startswith("use_spray_callback:"))
async def callback_use_spray(callback: types.CallbackQuery, get_user, save_db):
    _, owner_id = callback.data.split(":")
    if callback.from_user.id != int(owner_id):
        return await callback.answer("Это не твой спрей!", show_alert=True)
    user = await get_user(callback.from_user.id, callback.from_user.username)
    current_time = time.time()
    if current_time < user.get("belt_expire_time", 0):
        return await callback.answer("Пояс верности мешает использовать спрей! 🔒", show_alert=True)
    chat_id = str(callback.message.chat.id)
    inv = ensure_inv_dict(user)
    buffs = get_user_buffs(user)
    current_cooldown = int(1800 / buffs["stamina_multiplier"])
    chat_stats = user.get("chats_data", {}).get(chat_id)
    if not chat_stats: return await callback.answer("Ошибка данных чата.")
    last_time = chat_stats.get("last_droch_time", 0)
    if (current_time - last_time) < current_cooldown:
        inv["💦"] -= 1
        chat_stats["last_droch_time"] = 0
        await save_db(callback.from_user.id, user)
        await callback.message.edit_text("Ты применил спрей. 👍 Жми: /drochnut")
    else:
        await callback.answer("Спрей тебе сейчас не нужен!")


@router.message(Command("drochnut", "дрочнуть"))
async def cmd_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)


@router.message(F.text.lower().in_({"дрочнуть", "юз рука", "юз хуй", "дрочить", "юз 🍌"}))
async def text_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)


@router.message(F.text.lower() == "юз 💦")
async def use_spray_cmd(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    current_time = time.time()
    if current_time < user.get("belt_expire_time", 0):
        return await message.reply("Пояс верности мешает использовать спрей! 🔒")
    chat_id = str(message.chat.id)
    inv = ensure_inv_dict(user)
    buffs = get_user_buffs(user)
    current_cooldown = int(1800 / buffs["stamina_multiplier"])
    if inv.get("💦", 0) <= 0: return await message.reply("У тебя нет Спрея!")
    chat_stats = user.get("chats_data", {}).get(chat_id, {"last_droch_time": 0})
    if (current_time - chat_stats["last_droch_time"]) < current_cooldown:
        inv["💦"] -= 1
        chat_stats["last_droch_time"] = 0
        await save_db(message.from_user.id, user)
        await message.reply("Ты применил <b>спрей</b>! 🌼 Жми: /drochnut", parse_mode="HTML")
    else:
        await message.reply("Спрей сейчас не нужен!")

