import asyncio
import random
import time
import math
import html

from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from items import GAME_ITEMS

# Подключаем роутер
router = Router()

# ==========================================
# 1. СТРУКТУРА ПРЕДМЕТОВ (Имитация твоего GAME_ITEMS)
# ==========================================
GAME_ITEMS = {
    "💰": {"name": "ФармКоин"},
    "💐": {"name": "Букет цветов: К 8 марта"},
    # Предметы лукошка мы не добавляем сюда, чтобы они не засоряли общий инвентарь (или добавляй, если хочешь)
    # "🪻": {"name": "Гиацинт"},
    # "🌺": {"name": "Гибискус"},
    # "🫘": {"name": "Семена розы"},
    # "🌻": {"name": "Подсолнух"},
    # "🌹": {"name": "Роза"},
    # "🌷": {"name": "Тюльпан"},
    # "💧": {"name": "Вода"}
}

ITEMS_PER_PAGE = 15
FARMCOIN_EMOJI = "💰"

# ==========================================
# 2. ИМИТАЦИЯ ТВОЕЙ БД
# ==========================================
users_db = {}


def get_user_db(user_id: int):
    if user_id not in users_db:
        users_db[user_id] = {
            # Твой основной инвентарь
            "inventory": {"💰": 100},

            # Лукошко для ивента (отдельно от основного инвентаря)
            "lyk": {"🪻": 0, "🌺": 0, "🫘": 0, "🌻": 0, "🌹": 0, "🌷": 0, "💧": 5},

            # Сад
            "garden": {
                "seeds_planted": 0,
                "plant_timestamp": 0,
                "watered": False
            },

            # Ачивки
            "achievements": []
        }
    return users_db[user_id]


# Dependency Injection / Middleware заглушка
def get_user(user_id):
    return get_user_db(user_id)


# ==========================================
# 3. ТВОЙ ИНВЕНТАРЬ (Адаптированный)
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
    # Адаптировано под вызов без get_user в аргументах Aiogram (если ты не юзаешь Middleware)
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

# Команда Лукошко
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


# Команда для поиска цветов
@router.message(Command("find_flowers"))
async def find_flowers_command(message: Message):
    user = get_user(message.from_user.id)

    if random.random() <= 0.5:
        hyacinth = random.randint(2, 4)
        hibiscus = random.randint(4, 6)
        seeds = random.randint(1, 3)
        sunflower = 1

        user["lyk"]["🪻"] += hyacinth
        user["lyk"]["🌺"] += hibiscus
        user["lyk"]["🫘"] += seeds
        user["lyk"]["🌻"] += sunflower

        await message.reply(
            f"Ты аккуратно собрал в лукошко:\n"
            f"🪻 Гиацинт: {hyacinth}\n"
            f"🌺 Гибискус: {hibiscus}\n"
            f"🫘 Семена розы: {seeds}\n"
            f"🌻 Подсолнух: {sunflower}"
        )
    else:
        await message.reply("Ты погулял по поляне, но ничего не нашел. Попробуй еще раз!")


# Вспомогательная команда для посадки
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
        await message.reply("У тебя уже засажена клумба. Сначала собери цветы!")
        return

    user["lyk"]["🫘"] -= amount
    user["garden"]["seeds_planted"] = amount
    user["garden"]["plant_timestamp"] = time.time()
    user["garden"]["watered"] = False

    await message.reply(f"Ты успешно посадил {amount} 🫘!")


# Команда Сада
@router.message(Command("flowers"))
@router.message(F.text.lower() == "мой сад")
async def my_garden(message: Message):
    user = get_user(message.from_user.id)
    garden = user["garden"]
    seeds = garden["seeds_planted"]

    if seeds == 0:
        await message.reply("Твой сад\n\nПустой\n🟫🟫🟫🟫🟫🟫\n\nПосади семена командой /plant [кол-во]")
        return

    grow_time_seconds = 25 * 60
    if garden["watered"]:
        grow_time_seconds -= 10 * 60

    time_elapsed = time.time() - garden["plant_timestamp"]
    is_ready = time_elapsed >= grow_time_seconds
    watered_text = "Да" if garden["watered"] else "Нет"

    plant_emoji = "🌹" if is_ready else "🌱"
    visual_plants = plant_emoji * min(seeds, 6)
    visual_ground = "🟫" * min(seeds, 6)

    if not is_ready:
        text = f"_Твой сад_\n\n{visual_plants}\n{visual_ground}\nСтатус: Рост\nПолито: {watered_text}"
    else:
        text = f"_Твой сад_\n\n{visual_plants}\n{visual_ground}\nСтатус: Можно собирать. Жми: /Collect_flawers\nПолито: {watered_text}"

    await message.reply(text, parse_mode=ParseMode.MARKDOWN)


# Полив клумбы
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
    await message.reply("Ты успешно полил свою клумбу -10минут к росту цветов")


# Сбор урожая
@router.message(Command("Collect_flawers", ignore_case=True))
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

    user["garden"] = {
        "seeds_planted": 0,
        "plant_timestamp": 0,
        "watered": False
    }

    if tulips_grown > 0:
        await message.reply(
            f"Ты успешно собрал {roses_grown} роз, \n"
            f"А ещё у тебя вырос тюльпан ({tulips_grown} шт.) и ты положил их в лукошко!"
        )
    else:
        await message.reply(f"Ты успешно собрал {roses_grown} роз в лукошко!")


# Крафт букета (ИНТЕГРАЦИЯ В ОСНОВНОЙ ИНВЕНТАРЬ)
@router.message(Command("craft_bouquet"))
@router.message(F.text.lower() == "скрафтить букет")
async def craft_bouquet(message: Message):
    user = get_user(message.from_user.id)
    lyk = user["lyk"]
    inv = ensure_inv_dict(user)  # Подтягиваем основной инвентарь

    # Проверка наличия нужных цветов в лукошке
    if lyk["🌹"] >= 50 and lyk["🌻"] >= 1 and lyk["🌷"] >= 5:
        # Списываем ресурсы
        lyk["🌹"] -= 50
        lyk["🌻"] -= 1
        lyk["🌷"] -= 5

        # Выдаем предмет в основной инвентарь (ключ "💐")
        if "💐" not in inv:
            inv["💐"] = 0
        inv["💐"] += 1

        response_text = "Ты успешно скрафтил 💐 *Букет цветов: К 8 марта*! Он добавлен в твой основной инвентарь (/inv)."

        # Проверяем и выдаем ачивку
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


