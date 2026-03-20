import html
import uuid
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from items import GAME_ITEMS

router = Router()


# Функция для безопасного получения инвентаря в виде словаря
def get_inv_dict(user) -> dict:
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


# Вспомогательная функция для синхронизации рюкзаков
def ensure_backpacks(user):
    inv = get_inv_dict(user)
    backpack_count = inv.get("🎒", 0)
    if "backpacks" not in user:
        user["backpacks"] = []

    # Добавляем объекты рюкзаков, если их меньше чем иконок в инвентаре
    while len(user["backpacks"]) < backpack_count:
        user["backpacks"].append({
            "id": str(uuid.uuid4())[:16],
            "name": f"Рюкзак {len(user['backpacks']) + 1}",
            "items": {}
        })

    # Если рюкзаков в списке больше (получил передачей), подтягиваем инвентарь
    if len(user["backpacks"]) > backpack_count:
        inv["🎒"] = len(user["backpacks"])

    if not user.get("active_backpack_id") and user["backpacks"]:
        user["active_backpack_id"] = user["backpacks"][0]["id"]
    return user["backpacks"]


@router.message(Command("give", "обмен", "передать"))
@router.message(F.text.lower().startswith("дать "))
async def cmd_give_item(message: types.Message, get_user, save_db, command: CommandObject = None):
    args = []
    if command and command.args:
        args = command.args.split()
    else:
        parts = message.text.split()
        if len(parts) > 1:
            args = parts[1:]

    if not args:
        await message.answer(
            "ℹ️ <b>Как передать предмет:</b>\n\n"
            "<b>Вариант А (ответом):</b> <code>дать 🍹 5</code>\n"
            "<b>Вариант Б (по ID):</b> <code>дать 🍹 5 1234567</code>",
            parse_mode="HTML"
        )
        return

    item_emoji = args[0]
    if item_emoji not in GAME_ITEMS:
        return await message.answer("❌ Такого предмета не существует.")

    # Количество
    amount = 1
    if len(args) >= 2:
        try:
            amount = int(args[1])
            if amount <= 0: return await message.answer("❌ Введи число больше 0.")
        except ValueError:
            pass

    # Цель
    target_user_id = None
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    elif len(args) >= 3:
        try:
            target_user_id = int(args[2])
        except ValueError:
            return await message.answer("❌ Неверный формат ID.")

    if not target_user_id or target_user_id == message.from_user.id:
        return await message.answer("❌ Нельзя передать самому себе или цель не найдена.")

    # Получаем данные
    sender_user = await get_user(message.from_user.id, message.from_user.username)
    target_user = await get_user(target_user_id)

    if not target_user:
        return await message.answer("❌ Пользователь не найден в базе.")

    sender_inv = get_inv_dict(sender_user)
    target_inv = get_inv_dict(target_user)

    # --- СПЕЦИАЛЬНАЯ ЛОГИКА ДЛЯ РЮКЗАКА ---
    if item_emoji == "🎒":
        ensure_backpacks(sender_user)
        ensure_backpacks(target_user)

        active_id = sender_user.get("active_backpack_id")
        bp_idx = next((i for i, b in enumerate(sender_user["backpacks"]) if b["id"] == active_id), -1)

        if bp_idx == -1:
            return await message.answer("❌ У тебя нет активного рюкзака для передачи.")

        # Забираем рюкзак у отправителя
        bp_to_move = sender_user["backpacks"].pop(bp_idx)
        sender_inv["🎒"] = len(sender_user["backpacks"])
        if sender_inv["🎒"] <= 0: del sender_inv["🎒"]

        # Считаем сумму вещей внутри рюкзака
        total_items_in_bp = sum(bp_to_move["items"].values())

        # Отдаем рюкзак получателю
        target_user["backpacks"].append(bp_to_move)
        target_inv["🎒"] = len(target_user["backpacks"])

        # Обновляем активные ID
        sender_user["active_backpack_id"] = sender_user["backpacks"][0]["id"] if sender_user["backpacks"] else None
        target_user["active_backpack_id"] = bp_to_move["id"]

        await save_db(message.from_user.id, sender_user)
        await save_db(target_user_id, target_user)

        target_name = html.escape(
            message.reply_to_message.from_user.first_name if message.reply_to_message else f"ID {target_user_id}")
        return await message.answer(
            f"✅ Передан рюкзак <b>«{html.escape(bp_to_move['name'])}»</b> [{total_items_in_bp}] игроку {target_name}!",
            parse_mode="HTML"
        )

    # --- ТВОЙ ОРИГИНАЛЬНЫЙ КОД ДЛЯ ОСТАЛЬНЫХ ПРЕДМЕТОВ ---
    current_count = sender_inv.get(item_emoji, 0)
    if current_count < amount:
        return await message.answer(f"❌ У тебя нет столько {item_emoji} (в наличии: {current_count})")

    sender_inv[item_emoji] -= amount
    target_inv[item_emoji] = target_inv.get(item_emoji, 0) + amount

    if sender_inv[item_emoji] <= 0:
        del sender_inv[item_emoji]

    await save_db(message.from_user.id, sender_user)
    await save_db(target_user_id, target_user)

    item_name = GAME_ITEMS[item_emoji].get("name", "предмет")
    target_name = html.escape(
        message.reply_to_message.from_user.first_name if message.reply_to_message else f"ID {target_user_id}")

    await message.answer(
        f"{target_name} получил предмет <b>{amount} {item_emoji} {item_name}</b>.",
        parse_mode="HTML"
    )