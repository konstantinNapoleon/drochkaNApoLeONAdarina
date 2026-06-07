import random
import uuid
import time
from aiogram import Router, types, F
from aiogram.filters import Command

router = Router()

# 10 подарков на 1 500 000 ФК (из items.py)
BANT_GIFTS = [
    {"item": "📓", "name": "Инструкция по дрочкам от Наставника", "value": 150000},
    {"item": "🔍", "name": "Супер-лупа-подзалупа", "value": 150000},
    {"item": "📍", "name": "Чупик", "value": 125000},
    {"item": "🔌", "name": "Вилка для Автодрочера", "value": 120000},
    {"item": "🧿", "name": "Амулет греков", "value": 115000},
    {"item": "🧱", "name": "Кирпич", "value": 115000},
    {"item": "🎱", "name": "Шар №8", "value": 110000},
    {"item": "🎩", "name": "Цилиндр", "value": 110000},
    {"item": "🤖", "name": "Avtorob 3.14", "value": 180000},
    {"item": "🔎", "name": "Лупа-подзалупа", "value": 175000},
]

BANT_COOLDOWN = 24 * 60 * 60  # 24 часа в секундах


def ensure_inv_dict(user) -> dict:
    """Гарантирует, что инвентарь — словарь"""
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


def get_bant_kalendars(user):
    """Получает список календарей пользователя"""
    return user.get("bant_kalendars", [])


def create_new_bant(user):
    """Создаёт новый календарь с UUID"""
    kalendars = get_bant_kalendars(user)
    new_kalendar = {
        "uuid": f"s_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}_{uuid.uuid4().hex[:4]}_{uuid.uuid4().hex[:4]}_{uuid.uuid4().hex[:12]}",
        "gifts_left": 10,
        "opened": [],  # индексы открытых подарков
        "last_open": 0
    }
    kalendars.append(new_kalendar)
    user["bant_kalendars"] = kalendars
    return new_kalendar


@router.message(Command("bant"))
async def bant_list(message: types.Message, get_user, save_db):
    """Показывает все календари пользователя со ссылками для выбора"""
    user = await get_user(message.from_user.id, message.from_user.username)
    kalendars = get_bant_kalendars(user)

    if not kalendars:
        return await message.answer(
            "🎀 У тебя нет Адвент-календарей Бант!\n"
            "Купи в магазине командой /shop"
        )

    text = "🎀 <b>Адвент-календарь Бант</b>\n"
    text += "Кто прочёл — гей\n\n"
    text += "♡ AdeLiS ♡\n"
    text += "/select 💝\n\n"
    text += "Для выбора активного предмета вызови соответствую команду ✨\n\n"

    for i, kal in enumerate(kalendars, 1):
        status = "[ активен сейчас ✅ ]" if i == 1 else " "
        command = f"/s_{kal['uuid']}"

        text += f"{i}. {status}💝 Адвент-календарь Lite: 10 подарков (осталось {kal['gifts_left']}) — {command}\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/s_"))
async def bant_open(message: types.Message, get_user, save_db):
    """Открывает подарок в выбранном календаре"""
    uuid_part = message.text.replace("/s_", "").strip()
    user = await get_user(message.from_user.id, message.from_user.username)
    kalendars = get_bant_kalendars(user)

    # Ищем календарь по UUID
    selected = None
    selected_index = -1
    for idx, kal in enumerate(kalendars):
        if kal["uuid"] == uuid_part:
            selected = kal
            selected_index = idx
            break

    if not selected:
        return await message.answer("❌ Календарь не найден!")

    if selected["gifts_left"] <= 0:
        return await message.answer("❌ Этот календарь уже пуст!")

    now = int(time.time())
    time_passed = now - selected["last_open"]

    if time_passed < BANT_COOLDOWN and selected["last_open"] > 0:
        remaining = BANT_COOLDOWN - time_passed
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        return await message.answer(
            f"⏳ КД 24 часа!\n"
            f"Повтори через: {hours:02d}:{minutes:02d}"
        )

    # Открываем подарок
    available_gifts = [i for i in range(10) if i not in selected["opened"]]
    if not available_gifts:
        return await message.answer("❌ Все подарки открыты!")

    gift_index = random.choice(available_gifts)
    gift = BANT_GIFTS[gift_index]

    # Добавляем предмет в инвентарь
    inv = ensure_inv_dict(user)
    inv[gift["item"]] = inv.get(gift["item"], 0) + 1

    # Обновляем календарь
    selected["opened"].append(gift_index)
    selected["gifts_left"] -= 1
    selected["last_open"] = now
    user["bant_kalendars"] = kalendars

    await save_db(message.from_user.id, user)

    # Удаляем календарь если пуст
    if selected["gifts_left"] <= 0:
        kalendars.remove(selected)
        user["bant_kalendars"] = kalendars
        await save_db(message.from_user.id, user)

    await message.answer(
        f"🎀 <b>Ты открыл Адвент-календарь Бант!</b>\n\n"
        f"🎁 Награда: <b>{gift['item']} {gift['name']}</b>\n"
        f"💰 Стоимость: <b>{gift['value']:,} ФК</b>\n\n"
        f"📦 Осталось подарков: <b>{selected['gifts_left']}</b>",
        parse_mode="HTML"
    )


@router.message(Command("bant_force"))
async def bant_force_create(message: types.Message, get_user, save_db):
    """Тестовая команда: создаёт новый календарь"""
    user = await get_user(message.from_user.id, message.from_user.username)
    new_kal = create_new_bant(user)
    await save_db(message.from_user.id, user)

    await message.answer(
        f"✅ Создан новый календарь Бант!\n"
        f"UUID: <code>{new_kal['uuid']}</code>\n"
        f"Подарков: 10\n\n"
        f"Используй /bant для просмотра"
    )


@router.message(Command("select"))
async def select_command(message: types.Message, get_user, save_db):
    """Команда /select — показывает календари"""
    await bant_list(message, get_user, save_db)