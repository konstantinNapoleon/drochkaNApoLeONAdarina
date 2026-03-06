import asyncio
import random
import time
import math
import html
from datetime import datetime

from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode


# Подключаем роутер
router = Router()

# ==========================================
# 1. СТРУКТУРА ПРЕДМЕТОВ И ПРОМОКОДОВ
# ==========================================
GAME_ITEMS = {
    "💰": {"name": "ФармКоин"},
    "💐": {
        "name": "Букет цветов: К 8 марта",
        "description": "Подарок к 8 марта.",
        "price": 0,
        "emoji": "💐"
    },
}

ITEMS_PER_PAGE = 15
FARMCOIN_EMOJI = "💰"

# Список активных промокодов и наград за них
PROMOCODES = {
    "START": {
        "rewards": {"🌹": 15, "🌷": 5, "🫘": 10, "💧": 3},
        "description": "Стартовый набор садовода"
    },
    "SPRING2024": {
        "rewards": {"🌻": 2, "💧": 5},
        "description": "Весенний бонус"
    }
}

# ==========================================
# 2. ИМИТАЦИЯ БД
# ==========================================
users_db = {}


def get_user_db(user_id: int):
    if user_id not in users_db:
        users_db[user_id] = {
            "inventory": {"💰": 100},
            "lyk": {"🪻": 0, "🌺": 0, "🫘": 0, "🌻": 0, "🌹": 0, "🌷": 0, "💧": 5},
            "garden": {
                "seeds_planted": 0,
                "plant_timestamp": 0,
                "watered": False
            },
            "achievements": [],
            "used_promos": []  # Список использованных промокодов
        }
    return users_db[user_id]


def get_user(user_id):
    return get_user_db(user_id)


# ==========================================
# 3. ИНВЕНТАРЬ
# ==========================================
def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        inv = {}
        user["inventory"] = inv
    return inv


def get_inventory_data(user_inventory: dict):
    formatted_items = []
    for item_emoji, count in user_inventory.items():
        if count <= 0: continue
        item_info = GAME_ITEMS.get(item_emoji, {"name": "Неизвестный предмет"})
        item_name = item_info.get("name", "Неизвестный предмет")
        if item_emoji == FARMCOIN_EMOJI:
            continue
        formatted_items.append(f"• {count} {item_emoji} {html.escape(item_name)}")
    formatted_items.sort()
    return formatted_items


def create_inventory_kb(current_page: int, total_pages: int):
    builder = InlineKeyboardBuilder()
    buttons = []
    if current_page > 0:
        buttons.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"inv_page_{current_page - 1}"))
    buttons.append(types.InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="none"))
    if current_page < total_pages - 1:
        buttons.append(types.InlineKeyboardButton(text="➡️", callback_data=f"inv_page_{current_page + 1}"))
    builder.row(*buttons)
    builder.row(types.InlineKeyboardButton(text="❌ Закрыть", callback_data="inv_close"))
    return builder.as_markup()


@router.message(Command("inventory", "инв", "inv"))
async def cmd_inventory_grid(message: types.Message):
    user = get_user(message.from_user.id)
    inv_dict = ensure_inv_dict(user)
    farmcoin_count = inv_dict.get(FARMCOIN_EMOJI, 0)
    formatted_items = get_inventory_data(inv_dict)

    if not formatted_items and farmcoin_count <= 0:
        await message.answer("🎒 <b>Твой инвентарь пуст!</b>", parse_mode=ParseMode.HTML)
        return

    total_pages = max(1, math.ceil(len(formatted_items) / ITEMS_PER_PAGE))
    page_items = formatted_items[:ITEMS_PER_PAGE]
    inventory_render = "\n".join(page_items) if page_items else "<i>Предметов нет</i>"
    name = html.escape(message.from_user.first_name or "Игрок")

    response = (
        f"Твой инвентарь 👌 {name}\n\n"
        f"{FARMCOIN_EMOJI} ФармКоин: <b>{farmcoin_count}</b>\n"
        f"{inventory_render}"
    )
    await message.answer(response, parse_mode=ParseMode.HTML, reply_markup=create_inventory_kb(0, total_pages))


# ==========================================
# 4. ИВЕНТ САД И ЛУКОШКО
# ==========================================

@router.message(Command("lyk"))
async def show_lyk(message: Message):
    user = get_user(message.from_user.id)
    inv = user["lyk"]
    text = (
        f"🧺 *Твое лукошко:*\n\n"
        f"🪻 Гиацинты: {inv['🪻']}\n"
        f"🌺 Гибискусы: {inv['🌺']}\n"
        f"🫘 Семена розы: {inv['🫘']}\n"
        f"🌻 Подсолнухи: {inv['🌻']}\n"
        f"🌹 Розы: {inv['🌹']}\n"
        f"🌷 Тюльпаны: {inv['🌷']}\n"
        f"💧 Вода: {inv['💧']}"
    )
    await message.reply(text, parse_mode=ParseMode.MARKDOWN)


def get_current_flower_chance() -> float:
    current_hour = datetime.now().hour
    if current_hour % 2 == 0:
        return 1.0  # 100%
    else:
        return 0.2  # 20%


@router.message(Command("find_flowers"))
async def find_flowers_command(message: Message):
    if message.chat.username != "flowers_pol_doch":
        await message.reply("🌸 Собирать цветы можно только на поляне:\n👉 https://t.me/flowers_pol_doch")
        return

    user = get_user(message.from_user.id)
    chance = get_current_flower_chance()

    if random.random() <= chance:
        flower_types = [
            ("🪻", "Гиацинт", lambda: random.randint(2, 4)),
            ("🌺", "Гибискус", lambda: random.randint(4, 6)),
            ("🫘", "Семена для розы", lambda: random.randint(1, 3)),
            ("🌻", "Подсолнух", lambda: 1)
        ]

        emoji, name, count_func = random.choice(flower_types)
        amount = count_func()

        user["lyk"][emoji] += amount

        success_phrases = [
            f"<i>Разгребая густую траву, ты замечаешь что-то яркое... Ого, да это же...</i>\n\n🌾 {emoji} <b>{name}</b> (+{amount})\n\n<i>Они отправляются прямиком в лукошко!</i>",
            f"<i>Ты долго бродил по поляне, слушая пение птиц, как вдруг у твоих ног блеснуло сокровище природы...</i>\n\n✨ {emoji} <b>{name}</b> в количестве <b>{amount} шт.</b>!\n\n<i>Отличная находка!</i>",
            f"<i>Лёгкий ветерок донёс приятный аромат. Ты пошёл на запах и сорвал...</i>\n\n🍃 {emoji} <b>{name}</b> (x{amount})\n\n<i>Аккуратно убираем в корзинку.</i>",
            f"<i>Споткнувшись о корень дерева, ты упал прямо в кусты. Зато нашёл...</i>\n\n🌿 {emoji} <b>{name}</b> (Собрано: {amount})\n\n<i>Нет худа без добра!</i>"
        ]

        text = (
            "╭ 🌸 <b>ПРОГУЛКА ПО ПОЛЯНЕ</b>\n"
            "│\n"
            f"╰ {random.choice(success_phrases)}"
        )

        await message.reply(text, parse_mode=ParseMode.HTML)
    else:
        fail_phrases = [
            "<i>Ты обошел всю поляну, но нашел только старый рваный 👞 башмак...</i>\nПопробуй поискать еще!",
            "<i>Пчелы 🐝 прогнали тебя с цветочной поляны!</i>\nПридется вернуться позже.",
            "<i>Ты долго бродил, но все цветы кто-то собрал до тебя.</i>\nНе сдавайся, поищи еще!",
            "<i>Ты увлекся погоней за красивой бабочкой 🦋 и забыл, зачем пришел.</i>\nЛукошко осталось пустым."
        ]

        text = (
            "╭ 🍂 <b>ПУСТО...</b>\n"
            "│\n"
            f"╰ {random.choice(fail_phrases)}"
        )
        await message.reply(text, parse_mode=ParseMode.HTML)


# --- ПРОМОКОД С АРГУМЕНТОМ ---
@router.message(Command("promo"))
async def promo_command(message: Message):
    user = get_user(message.from_user.id)

    # Получаем текст после команды
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("📝 <b>Использование:</b> <code>/promo [слово]</code>", parse_mode=ParseMode.HTML)
        return

    promo_code = args[1].strip().upper()  # Переводим в верхний регистр для удобства

    if promo_code not in PROMOCODES:
        await message.reply("❌ <b>Такого промокода не существует!</b>", parse_mode=ParseMode.HTML)
        return

    if promo_code in user["used_promos"]:
        await message.reply("⚠️ <b>Ты уже использовал этот промокод!</b>", parse_mode=ParseMode.HTML)
        return

    # Выдаем награды
    promo_data = PROMOCODES[promo_code]
    rewards_text = ""

    for item_emoji, amount in promo_data["rewards"].items():
        user["lyk"][item_emoji] += amount
        rewards_text += f"{item_emoji} <b>{amount} шт.</b>\n"

    user["used_promos"].append(promo_code)

    text = (
        "🎁 <b>ПРОМОКОД АКТИВИРОВАН!</b> \n"
        "━━━━━━━━━━━━━━━\n"
        f"<i>{promo_data['description']}:</i>\n\n"
        f"{rewards_text}\n"
        "━━━━━━━━━━━━━━━\n"
        "<i>Проверь лукошко: /lyk</i>"
    )
    await message.reply(text, parse_mode=ParseMode.HTML)


@router.message(Command("plant"))
async def plant_seeds(message: Message):
    user = get_user(message.from_user.id)
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.reply("Используй: /plant [количество]")
        return

    amount = int(args[1])
    if user["lyk"]["🫘"] < amount:
        await message.reply("У тебя в лукошке недостаточно семян розы 🫘!")
        return

    if user["garden"]["seeds_planted"] > 0:
        await message.reply("У тебя уже засажена клумба. Сначала собери урожай!")
        return

    user["lyk"]["🫘"] -= amount
    user["garden"]["seeds_planted"] = amount
    user["garden"]["plant_timestamp"] = time.time()
    user["garden"]["watered"] = False
    await message.reply(f"Ты успешно посадил {amount} 🫘!")


@router.message(Command("flowers"))
@router.message(F.text.lower() == "мой сад")
async def my_garden(message: Message):
    user = get_user(message.from_user.id)
    garden = user["garden"]
    seeds = garden["seeds_planted"]

    if seeds == 0:
        text = (
            "🏡 <b>ТВОЙ САД</b> 🏡\n"
            "━━━━━━━━━━━━━━━\n"
            "<i>Ветер гуляет по пустой земле...</i>\n\n"
            "🟫 🟫 🟫 🟫 🟫 🟫\n\n"
            "🌱 <i>Здесь пока ничего не растёт.</i>\n"
            "👉 Посади семена: <code>/plant [кол-во]</code>\n"
            "━━━━━━━━━━━━━━━"
        )
        await message.reply(text, parse_mode=ParseMode.HTML)
        return

    grow_time_seconds = 25 * 60
    if garden["watered"]:
        grow_time_seconds -= 10 * 60

    time_elapsed = time.time() - garden["plant_timestamp"]
    is_ready = time_elapsed >= grow_time_seconds
    watered_text = "💦 Да" if garden["watered"] else "🏜 Нет"

    plant_emoji = "🌹" if is_ready else "🌱"
    visual_plants = " ".join([plant_emoji] * min(seeds, 6))
    visual_ground = " ".join(["🟫"] * min(seeds, 6))

    if not is_ready:
        status = "⏳ Набираются сил (Рост)"
    else:
        status = "✨ Можно собирать! 👉 /collect_flowers"

    text = (
        "🏡 <b>ТВОЙ САД</b> \n"
        "━━━━━━━━━━━━━━━\n\n"
        f"{visual_plants}\n"
        f"{visual_ground}\n\n"
        f"📈 <b>Статус:</b> {status}\n"
        f"💧 <b>Полито:</b> {watered_text}\n"
        "━━━━━━━━━━━━━━━"
    )

    await message.reply(text, parse_mode=ParseMode.HTML)


@router.message(F.text.lower() == "полить клумбу")
async def water_garden(message: Message):
    user = get_user(message.from_user.id)
    garden = user["garden"]
    if garden["seeds_planted"] == 0:
        await message.reply("Твоя клумба пуста, нечего поливать.")
        return
    if garden["watered"]:
        await message.reply("Тебе не нужно поливать цветы, они уже политы!")
        return
    if user["lyk"]["💧"] < 1:
        await message.reply("У тебя в лукошке нет предмета 💧 Вода!")
        return

    user["lyk"]["💧"] -= 1
    garden["watered"] = True
    await message.reply("Ты успешно полил свою клумбу -10 минут к росту цветов")


@router.message(Command("collect_flowers", ignore_case=True))
async def collect_flowers(message: Message):
    user = get_user(message.from_user.id)
    garden = user["garden"]

    if garden["seeds_planted"] == 0:
        await message.reply("Твоя клумба пуста.")
        return

    grow_time_seconds = 25 * 60
    if garden["watered"]:
        grow_time_seconds -= 10 * 60

    time_elapsed = time.time() - garden["plant_timestamp"]
    if time_elapsed < grow_time_seconds:
        await message.reply("Цветы еще не выросли!")
        return

    seeds = garden["seeds_planted"]
    roses_grown = seeds
    tulips_grown = 0
    for _ in range(seeds):
        if random.random() <= 0.35:
            tulips_grown += 1

    user["lyk"]["🌹"] += roses_grown
    user["lyk"]["🌷"] += tulips_grown
    user["garden"] = {"seeds_planted": 0, "plant_timestamp": 0, "watered": False}

    if tulips_grown > 0:
        await message.reply(
            f"Ты успешно собрал {roses_grown} роз 🌹, \n"
            f"А ещё у тебя вырос тюльпан ({tulips_grown} шт.) и ты положил их в лукошко!"
        )
    else:
        await message.reply(f"Ты успешно собрал {roses_grown} роз 🌹 в лукошко!")


@router.message(Command("craft_bouquet"))
@router.message(F.text.lower() == "скрафтить букет")
async def craft_bouquet(message: Message):
    user = get_user(message.from_user.id)
    lyk = user["lyk"]
    inv = ensure_inv_dict(user)

    if lyk["🌹"] >= 50 and lyk["🌻"] >= 1 and lyk["🌷"] >= 5:
        lyk["🌹"] -= 50
        lyk["🌻"] -= 1
        lyk["🌷"] -= 5

        if "💐" not in inv:
            inv["💐"] = 0
        inv["💐"] += 1

        response_text = "Ты успешно скрафтил 💐 *Букет цветов: К 8 марта*! Он добавлен в твой основной инвентарь (/inv)."
        if "🌹: Настоящий садовод" not in user["achievements"]:
            user["achievements"].append("🌹: Настоящий садовод")
            response_text += "\n\n🏆 *Получена новая ачивка:* 🌹 Настоящий садовод!"

        await message.reply(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply(
            "Тебе не хватает цветов для крафта букета!\n\n"
            "Требуется:\n"
            "🌹 Розы: 50\n"
            "🌻 Подсолнух: 1\n"
            "🌷 Тюльпаны: 5\n\n"
            f"У тебя в лукошке: 🌹 {lyk['🌹']}, 🌻 {lyk['🌻']}, 🌷 {lyk['🌷']}."
        )


