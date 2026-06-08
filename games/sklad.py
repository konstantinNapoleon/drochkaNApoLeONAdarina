import html
import random
import string
from aiogram import Router, types, F
from aiogram.filters import Command
from items import GAME_ITEMS

router = Router()

BACKPACK_EMOJI = "🎒"


def generate_backpack_id():
    parts = [
        ''.join(random.choices(string.hexdigits.lower(), k=8)),
        ''.join(random.choices(string.hexdigits.lower(), k=4)),
        ''.join(random.choices(string.hexdigits.lower(), k=4)),
        ''.join(random.choices(string.hexdigits.lower(), k=4)),
        ''.join(random.choices(string.hexdigits.lower(), k=12))
    ]
    return f"s_{'_'.join(parts)}"


def get_backpacks(user_data):
    if "backpacks" not in user_data:
        user_data["backpacks"] = {}
    if isinstance(user_data["backpacks"], list):
        user_data["backpacks"] = {}
    return user_data["backpacks"]


def get_active_backpack(user_data):
    backpacks = get_backpacks(user_data)
    active_id = user_data.get("active_backpack_id")

    if active_id and active_id in backpacks:
        return backpacks[active_id], active_id

    if not backpacks:
        bp_id = generate_backpack_id()
        backpacks[bp_id] = {"name": "Рюкзак: С вещами", "items": {}}
        user_data["active_backpack_id"] = bp_id
        return backpacks[bp_id], bp_id

    first_id = list(backpacks.keys())[0]
    user_data["active_backpack_id"] = first_id
    return backpacks[first_id], first_id


def create_backpack(user_data, name="Новый рюкзак"):
    backpacks = get_backpacks(user_data)
    bp_id = generate_backpack_id()
    backpacks[bp_id] = {"name": name, "items": {}}
    return bp_id


# ========== ХЕНДЛЕРЫ ==========

@router.message(F.text.lower() == "юз 🎒")
async def use_backpack_show(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    if not user:
        return await message.reply("❌ Ошибка.")

    backpack, bp_id = get_active_backpack(user)
    items = backpack.get("items", {})

    if not items:
        return await message.reply(
            f"🎒 <b>{backpack['name']}</b> [пуст]\n\n"
            f"<i>Положи: <code>юз 🎒 + 🏆 5</code></i>",
            parse_mode="HTML"
        )

    items_list = [f"{count} {emoji}" for emoji, count in items.items()]
    text = f"🎒 <b>Содержимое {backpack['name']}</b>\n\n{', '.join(items_list)}"
    await message.reply(text, parse_mode="HTML")


@router.message(F.text.lower().startswith("юз 🎒 + "))
async def use_backpack_put(message: types.Message, get_user, save_db):
    try:
        parts = message.text.split(" + ", 1)[1].strip().split()
    except:
        return await message.reply("❌ Ошибка команды.")

    if not parts:
        return await message.reply("❌ Укажи предмет.")

    item_emoji = parts[0]
    quantity = 1

    if len(parts) > 1:
        try:
            quantity = int(parts[1])
        except:
            return await message.reply("❌ Неверное количество.")

    if item_emoji not in GAME_ITEMS:
        return await message.reply("❌ Такого предмета нет.")

    if item_emoji == BACKPACK_EMOJI:
        return await message.reply("❌ Нельзя положить рюкзак в рюкзак!")

    user = await get_user(message.from_user.id, message.from_user.username)
    if not user:
        return await message.reply("❌ Ошибка.")

    inv = user.get("inventory", {})
    available = inv.get(item_emoji, 0)

    if available <= 0:
        return await message.reply(f"❌ У тебя нет {item_emoji}.")

    if quantity > available:
        return await message.reply(f"❌ У тебя только {available} {item_emoji}.")

    # === ДОБАВИЛ ПОЛУЧЕНИЕ РЮКЗАКА ===
    backpack, bp_id = get_active_backpack(user)
    # ================================

    inv[item_emoji] -= quantity
    if inv[item_emoji] <= 0:
        del inv[item_emoji]

    backpack["items"][item_emoji] = backpack["items"].get(item_emoji, 0) + quantity

    await save_db(message.from_user.id, user)

    item_name = GAME_ITEMS[item_emoji].get("name", "Предмет")
    await message.reply(
        f"✅ <b>Положил в рюкзак {quantity} x {item_emoji} {item_name}!</b>",
        parse_mode="HTML"
    )


@router.message(F.text.lower().startswith("юз 🎒 - "))
async def use_backpack_take(message: types.Message, get_user, save_db):
    try:
        parts = message.text.split(" - ", 1)[1].strip().split()
    except:
        return await message.reply("❌ Ошибка команды.")

    if not parts:
        return await message.reply("❌ Укажи предмет.")

    item_emoji = parts[0]
    quantity = 1

    if len(parts) > 1:
        try:
            quantity = int(parts[1])
        except:
            return await message.reply("❌ Неверное количество.")

    user = await get_user(message.from_user.id, message.from_user.username)
    if not user:
        return await message.reply("❌ Ошибка.")

    backpack, bp_id = get_active_backpack(user)
    available = backpack["items"].get(item_emoji, 0)

    if available <= 0:
        return await message.reply(f"❌ В рюкзаке нет {item_emoji}.")

    if quantity > available:
        return await message.reply(f"❌ В рюкзаке только {available} {item_emoji}.")

    if "inventory" not in user:
        user["inventory"] = {}
    user["inventory"][item_emoji] = user["inventory"].get(item_emoji, 0) + quantity

    backpack["items"][item_emoji] -= quantity
    if backpack["items"][item_emoji] <= 0:
        del backpack["items"][item_emoji]

    await save_db(message.from_user.id, user)

    item_name = GAME_ITEMS[item_emoji].get("name", "Предмет")
    await message.reply(
        f"✅ <b>Взял {quantity} x {item_emoji} {item_name}!</b>",
        parse_mode="HTML"
    )


# ========== КОМАНДЫ ==========

@router.message(Command("backpacks", "рюкзаки"))
async def cmd_backpacks(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    if not user:
        return await message.reply("❌ Ошибка.")

    backpacks = get_backpacks(user)
    active_id = user.get("active_backpack_id")

    if not backpacks:
        bp_id = create_backpack(user, "Рюкзак: С вещами")
        user["active_backpack_id"] = bp_id
        await save_db(message.from_user.id, user)
        backpacks = get_backpacks(user)
        active_id = bp_id

    text = "<b>🎒 Твои рюкзаки:</b>\n\n"
    for i, (bp_id, bp_data) in enumerate(backpacks.items(), 1):
        mark = "✅ " if bp_id == active_id else ""
        count = sum(bp_data["items"].values())
        status = f"[{count}]" if count > 0 else "[пуст]"
        text += f"<b>{i}.</b> {mark}<b>{bp_data['name']}</b> {status}\n<code>/select {bp_id}</code>\n\n"

    await message.reply(text, parse_mode="HTML")


@router.message(Command("select"))
async def cmd_select(message: types.Message, get_user, save_db):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await cmd_backpacks(message, get_user, save_db)

    bp_id = args[1].strip()
    user = await get_user(message.from_user.id, message.from_user.username)
    if not user:
        return await message.reply("❌ Ошибка.")

    backpacks = get_backpacks(user)
    if bp_id not in backpacks:
        return await message.reply("❌ Рюкзак не найден.")

    user["active_backpack_id"] = bp_id
    await save_db(message.from_user.id, user)

    await message.reply(f"✅ <b>Выбран:</b> {backpacks[bp_id]['name']}", parse_mode="HTML")


@router.message(Command("newbackpack", "новыйрюкзак"))
async def cmd_new_backpack(message: types.Message, get_user, save_db):
    args = message.text.split(maxsplit=1)
    user = await get_user(message.from_user.id, message.from_user.username)
    if not user:
        return await message.reply("❌ Ошибка.")

    backpacks = get_backpacks(user)
    if len(backpacks) >= 10:
        return await message.reply("❌ Максимум 10 рюкзаков!")

    name = args[1].strip() if len(args) > 1 else f"Рюкзак #{len(backpacks) + 1}"
    bp_id = create_backpack(user, name)
    await save_db(message.from_user.id, user)

    await message.reply(
        f"✅ <b>Создан:</b> {name}\n<code>ID:</code> <code>{bp_id}</code>\n<code>/select {bp_id}</code>",
        parse_mode="HTML"
    )


@router.message(Command("renamebackpack", "переименоватьрюкзак"))
async def cmd_rename_backpack(message: types.Message, get_user, save_db):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("❌ Укажи имя.")

    user = await get_user(message.from_user.id, message.from_user.username)
    if not user:
        return await message.reply("❌ Ошибка.")

    backpack, bp_id = get_active_backpack(user)
    backpack["name"] = args[1].strip()
    await save_db(message.from_user.id, user)

    await message.reply(f"✅ <b>Переименован:</b> {backpack['name']}", parse_mode="HTML")


@router.message(F.text.lower() == "юз 🎒 хелп")
async def backpack_help(message: types.Message):
    text = (
        "<b>🎒 Рюкзаки:</b>\n\n"
        "<code>юз 🎒</code> — содержимое\n"
        "<code>юз 🎒 + 🏆</code> — положить 1 шт\n"
        "<code>юз 🎒 + 🏆 5</code> — положить 5 шт\n"
        "<code>юз 🎒 - 🏆</code> — взять 1 шт\n"
        "<code>юз 🎒 - 🏆 3</code> — взять 3 шт\n"
        "<code>/select (ID)</code> — выбрать\n"
        "<code>/backpacks</code> — список\n"
        "<code>/newbackpack</code> — создать"
    )
    await message.reply(text, parse_mode="HTML")