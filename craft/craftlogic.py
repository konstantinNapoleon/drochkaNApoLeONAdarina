import html
import asyncio
import logging
import time as t_lib
from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject
from .recipes import CRAFT_RECIPES  # Добавлена точка для работы внутри папки

router = Router()

# Временное хранилище активных крафтов {user_id: [список задач]}
ACTIVE_CRAFTS = {}


def get_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        user["inventory"] = {}
    return user["inventory"]


# ФОНОВАЯ ЗАДАЧА
async def delayed_craft_task(bot, user_id, item_emoji, total_amount, wait_seconds, get_user, save_db, task_info):
    try:
        # Ждем время
        await asyncio.sleep(wait_seconds)

        # Выдача предмета
        user = await get_user(user_id)
        if user:
            inv = get_inv_dict(user)
            inv[item_emoji] = inv.get(item_emoji, 0) + total_amount
            await save_db(user_id, user)

            # Уведомление в ЛС
            recipe_name = CRAFT_RECIPES[item_emoji]["name"]
            try:
                await bot.send_message(
                    user_id,
                    f"✅ <b>Крафт закончен!</b>\n"
                    f"Было скравчено: <b>{total_amount} {item_emoji} {recipe_name}</b>",
                    parse_mode="HTML"
                )
            except Exception:
                pass

    finally:
        # Очистка из списка активных в любом случае (даже при ошибке)
        if user_id in ACTIVE_CRAFTS:
            ACTIVE_CRAFTS[user_id] = [t for t in ACTIVE_CRAFTS[user_id] if t != task_info]
            if not ACTIVE_CRAFTS[user_id]:
                del ACTIVE_CRAFTS[user_id]


# КОМАНДА КРАФТА
@router.message(Command("craft"))
@router.message(F.text.lower().startswith("крафт "))
async def cmd_craft_logic(message: types.Message, get_user, save_db, command: CommandObject = None):
    user_id = message.from_user.id

    # Разбираем аргументы
    args = []
    if command and command.args:
        args = command.args.split()
    else:
        parts = message.text.split()
        if len(parts) > 1:
            args = parts[1:]

    # --- ЕСЛИ ПРОСТО /CRAFT — ПОКАЗЫВАЕМ АКТИВНЫЕ КРАФТЫ ---
    if not args:
        if user_id not in ACTIVE_CRAFTS or not ACTIVE_CRAFTS[user_id]:
            return await message.reply(
                "❌ <b>У тебя сейчас нет активных крафтов.</b>\n\n"
                "Чтобы что-то создать, используй:\n"
                "<code>крафт [предмет] [кол-во]</code>\n"
                "Например: <code>крафт 🚬 10</code>",
                parse_mode="HTML"
            )

        text = "⏳ <b>Твои текущие крафты:</b>\n\n"
        current_time = t_lib.time()

        for i, craft in enumerate(ACTIVE_CRAFTS[user_id], 1):
            remains = int(craft["end_time"] - current_time)
            if remains < 0: remains = 0

            # Формат времени
            m, s = divmod(remains, 60)
            time_str = f"{m}м {s}с" if m > 0 else f"{s}с"

            text += f"{i}. {craft['emoji']} <b>{craft['name']}</b> ({craft['amount']} шт.)\n"
            text += f"   Осталось: <code>{time_str}</code>\n\n"

        return await message.answer(text, parse_mode="HTML")

    # --- ЛОГИКА ЗАПУСКА КРАФТА ---
    item_emoji = args[0]
    try:
        count = int(args[1]) if len(args) > 1 else 1
        if count <= 0: return await message.reply("❌ Количество должно быть больше 0.")
    except ValueError:
        count = 1

    if item_emoji not in CRAFT_RECIPES:
        return await message.reply("❌ Такого рецепта не существует.")

    recipe = CRAFT_RECIPES[item_emoji]
    user = await get_user(user_id, message.from_user.username)
    inv = get_inv_dict(user)

    # Проверка ресурсов
    missing = []
    for ing, req in recipe["ingredients"].items():
        total = req * count
        if inv.get(ing, 0) < total:
            missing.append(f"{total - inv.get(ing, 0)}{ing}")

    if missing:
        return await message.reply(f"❌ Недостаточно ресурсов! Нужно еще: {', '.join(missing)}")

    # Списание
    for ing, req in recipe["ingredients"].items():
        inv[ing] -= (req * count)
        if inv[ing] <= 0: del inv[ing]

    await save_db(user_id, user)

    # Расчет времени
    wait_time = count * recipe.get("time", 10)
    end_time = t_lib.time() + wait_time

    # Сохраняем информацию о задаче
    task_info = {
        "emoji": item_emoji,
        "name": recipe["name"],
        "amount": count * recipe.get("amount", 1),
        "end_time": end_time
    }

    if user_id not in ACTIVE_CRAFTS:
        ACTIVE_CRAFTS[user_id] = []
    ACTIVE_CRAFTS[user_id].append(task_info)

    # Запуск
    asyncio.create_task(
        delayed_craft_task(
            message.bot, user_id, item_emoji,
            task_info["amount"], wait_time,
            get_user, save_db, task_info
        )
    )

    await message.reply(
        f"⚒️ <b>Крафт запущен!</b>\n"
        f"Ты создаешь {count} {item_emoji}\n"
        f"Будет готово через: <b>{wait_time // 60}м {wait_time % 60}с</b>",
        parse_mode="HTML"
    )


