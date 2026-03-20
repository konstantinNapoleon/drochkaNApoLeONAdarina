import html
import uuid
import re
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from items import GAME_ITEMS

router = Router()


# Вспомогательная функция для инвентаря
def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        user["inventory"] = {}
    return user["inventory"]


# Вспомогательная функция для инициализации рюкзаков
def ensure_backpacks(user):
    inv = ensure_inv_dict(user)
    backpack_count = inv.get("🎒", 0)

    if "backpacks" not in user:
        user["backpacks"] = []

    # Если рюкзаков в базе меньше, чем предметов 🎒 в инвентаре — добавляем новые пустые слоты
    while len(user["backpacks"]) < backpack_count:
        new_id = str(uuid.uuid4()).replace("-", "")[:32]
        user["backpacks"].append({
            "id": new_id,
            "name": f"Пустой {len(user['backpacks']) + 1}",
            "items": {}
        })

    # Если активный рюкзак не выбран или его ID не валиден
    if not user.get("active_backpack_id") and user["backpacks"]:
        user["active_backpack_id"] = user["backpacks"][0]["id"]

    return user["backpacks"]


def get_active_backpack(user):
    ensure_backpacks(user)
    active_id = user.get("active_backpack_id")
    for bp in user["backpacks"]:
        if bp["id"] == active_id:
            return bp
    if user["backpacks"]:
        return user["backpacks"][0]
    return None


# --- КОМАНДА /select 🎒 ---
@router.message(Command("select"))
async def cmd_select_backpack(message: types.Message, command: CommandObject, get_user):
    if not command.args or "🎒" not in command.args:
        return  # Можно добавить логику для других предметов здесь

    user = await get_user(message.from_user.id, message.from_user.username)
    ensure_backpacks(user)

    if not user["backpacks"]:
        return await message.reply("У тебя нет ни одного 🎒 Рюкзака!")

    lines = ["<b>Для выбора активного предмета вызови соответствующую команду 🐱</b>\n"]

    for i, bp in enumerate(user["backpacks"], 1):
        is_active = bp["id"] == user.get("active_backpack_id")
        status = "активен сейчас ✅" if is_active else "пуст" if not bp["items"] else f"С вещами [{len(bp['items'])}]"

        line = f"{i}. [" + status + f"] 🎒 <b>Рюкзак: {html.escape(bp['name'])}</b>"
        if not is_active:
            line += f"\n<code>/s_{bp['id']}</code>"
        lines.append(line)

    await message.answer("\n\n".join(lines), parse_mode="HTML")


# --- ОБРАБОТЧИК ДИНАМИЧЕСКИХ КОМАНД /s_UUID ---
@router.message(F.text.startswith("/s_"))
async def handle_select_link(message: types.Message, get_user, save_db):
    bp_id = message.text.split("_")[1].split("@")[0]  # Учитываем @bot_name
    user = await get_user(message.from_user.id, message.from_user.username)

    found_bp = None
    for bp in user.get("backpacks", []):
        if bp["id"] == bp_id:
            found_bp = bp
            break

    if found_bp:
        user["active_backpack_id"] = bp_id
        await save_db(message.from_user.id, user)
        await message.answer(
            f"Предмет 🎒 Рюкзак: <b>{html.escape(found_bp['name'])}</b> сделан активным! 🥳\n\n"
            "Теперь он будет использоваться в командах /use, /give и /trade.",
            parse_mode="HTML"
        )
    else:
        await message.reply("Рюкзак не найден или не принадлежит тебе.")


# --- КОМАНДА юз 🎒 (ОСНОВНАЯ ЛОГИКА) ---
@router.message(F.text.lower().startswith("юз 🎒"))
async def use_backpack_logic(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    text = message.text[4:].strip()
    inv = ensure_inv_dict(user)

    if inv.get("🎒", 0) <= 0:
        return await message.reply("❌ У тебя нет рюкзака!")

    active_bp = get_active_backpack(user)
    if not active_bp:
        return await message.reply("❌ Ошибка рюкзака. Попробуй /select 🎒")

    # 1. ХЕЛП
    if text.lower() == "хелп":
        help_text = (
            "<b>Инструкция по 🎒 Рюкзаку:</b>\n\n"
            "• <code>юз 🎒</code> — Содержимое активного рюкзака\n"
            "• <code>юз 🎒 +[предмет] [кол-во]</code> — Положить в рюкзак\n"
            "• <code>юз 🎒 -[предмет] [кол-во]</code> — Забрать из рюкзака\n"
            "• <code>юз 🎒 имя [новое имя]</code> — Переименовать рюкзак\n"
            "• <code>/select 🎒</code> — Список всех твоих рюкзаков\n\n"
            "Пример: <code>юз 🎒 +🔑 100</code>"
        )
        return await message.answer(help_text, parse_mode="HTML")

    # 2. ПЕРЕИМЕНОВАНИЕ
    if text.lower().startswith("имя "):
        new_name = text[4:].strip()
        if not new_name: return await message.reply("Укажи имя!")
        active_bp["name"] = new_name[:30]
        await save_db(message.from_user.id, user)
        return await message.reply(f"✅ Рюкзак переименован в «{html.escape(active_bp['name'])}»")

    # 3. ПОЛОЖИТЬ (+)
    if text.startswith("+"):
        match = re.match(r"\+([^\d\s\w\d]+)\s*(\d+)?", text)
        if not match: return await message.reply("Пример: <code>юз 🎒 +🔑 10</code>", parse_mode="HTML")

        emoji = match.group(1)
        amount = int(match.group(2)) if match.group(2) else 1

        if inv.get(emoji, 0) < amount:
            return await message.reply(f"❌ У тебя нет столько {emoji} в инвентаре!")

        # Перемещаем
        inv[emoji] -= amount
        active_bp["items"][emoji] = active_bp["items"].get(emoji, 0) + amount
        await save_db(message.from_user.id, user)
        return await message.reply(f"Ты успешно положил в рюкзак {emoji} ({amount} шт.)!")

    # 4. ЗАБРАТЬ (-)
    if text.startswith("-"):
        match = re.match(r"\-([^\d\s\w\d]+)\s*(\d+)?", text)
        if not match: return await message.reply("Пример: <code>юз 🎒 -🔑 10</code>", parse_mode="HTML")

        emoji = match.group(1)
        amount = int(match.group(2)) if match.group(2) else 1

        if active_bp["items"].get(emoji, 0) < amount:
            return await message.reply(f"❌ В рюкзаке нет столько {emoji}!")

        # Перемещаем обратно
        active_bp["items"][emoji] -= amount
        if active_bp["items"][emoji] <= 0: del active_bp["items"][emoji]
        inv[emoji] = inv.get(emoji, 0) + amount
        await save_db(message.from_user.id, user)
        return await message.reply(f"Ты успешно забрал из рюкзака {emoji} ({amount} шт.)!")

    # 5. ПРОСМОТР (Если просто юз 🎒)
    if not text:
        content = []
        # Сортировка по каталогу GAME_ITEMS
        for item_emoji in GAME_ITEMS.keys():
            count = active_bp["items"].get(item_emoji, 0)
            if count > 0:
                content.append(f"{count}{item_emoji}")

        # Добавляем то, чего нет в каталоге
        for emoji, count in active_bp["items"].items():
            if emoji not in GAME_ITEMS and count > 0:
                content.append(f"{count}{emoji}")

        if not content:
            result = f"Содержимое рюкзака «{html.escape(active_bp['name'])}» 💣\n\nПусто..."
        else:
            result = f"Содержимое рюкзака «{html.escape(active_bp['name'])}» 💣\n\n" + ", ".join(content)

        await message.answer(result, parse_mode="HTML")
