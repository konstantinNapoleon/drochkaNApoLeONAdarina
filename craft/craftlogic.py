import html
import asyncio
import logging
from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject
from .recipes import CRAFT_RECIPES
from items import GAME_ITEMS

router = Router()


# Функция для безопасного получения инвентаря
def get_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        user["inventory"] = {}
    return user["inventory"]


# ФОНОВАЯ ЗАДАЧА (ВЫДАЧА ПРЕДМЕТА)
async def delayed_craft_task(bot, user_id, item_emoji, total_amount, wait_seconds, get_user, save_db):
    try:
        # Ждем положенное время
        await asyncio.sleep(wait_seconds)

        # Загружаем актуального пользователя
        user = await get_user(user_id)
        if not user:
            return

        inv = get_inv_dict(user)

        # Выдаем предмет
        inv[item_emoji] = inv.get(item_emoji, 0) + total_amount

        # Сохраняем базу
        await save_db(user_id, user)

        # Отправляем уведомление в ЛС
        recipe_name = CRAFT_RECIPES[item_emoji]["name"]
        try:
            await bot.send_message(
                user_id,
                f"✅ <b>Крафт закончен!</b>\n"
                f"Было скравчено: <b>{total_amount} {item_emoji} {recipe_name}</b>",
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Не удалось отправить ЛС пользователю {user_id}: {e}")

    except Exception as global_e:
        logging.error(f"Ошибка в фоновом крафте: {global_e}")


# ОБРАБОТКА КОМАНДЫ КРАФТА
@router.message(Command("craft"))
@router.message(F.text.lower().startswith("крафт "))
async def cmd_craft_logic(message: types.Message, get_user, save_db, command: CommandObject = None):
    # Разбираем текст сообщения
    args = []
    if command and command.args:
        args = command.args.split()
    else:
        # Для обычного текста "крафт 🚬 10"
        parts = message.text.split()
        if len(parts) > 1:
            args = parts[1:]

    if not args:
        return await message.reply(
            "🛠 <b>Инструкция:</b>\n\n"
            "Используй: <code>крафт [предмет] [кол-во]</code>\n"
            "Например: <code>крафт 🚬 10</code>",
            parse_mode="HTML"
        )

    item_emoji = args[0]

    # Определяем количество (по умолчанию 1)
    try:
        count = int(args[1]) if len(args) > 1 else 1
        if count <= 0:
            return await message.reply("❌ Количество должно быть больше 0.")
    except ValueError:
        count = 1

    # Проверка существования рецепта
    if item_emoji not in CRAFT_RECIPES:
        return await message.reply("❌ Такого рецепта не существует. Проверь список в <code>юз 📘</code>")

    recipe = CRAFT_RECIPES[item_emoji]
    user = await get_user(message.from_user.id, message.from_user.username)
    inv = get_inv_dict(user)

    # 1. ПРОВЕРКА РЕСУРСОВ
    missing = []
    for ing, req_per_one in recipe["ingredients"].items():
        total_needed = req_per_one * count
        if inv.get(ing, 0) < total_needed:
            missing.append(f"{total_needed - inv.get(ing, 0)}{ing}")

    if missing:
        return await message.reply(f"❌ Недостаточно ресурсов! Нужно ещё: {', '.join(missing)}")

    # 2. СПИСАНИЕ РЕСУРСОВ (СРАЗУ)
    for ing, req_per_one in recipe["ingredients"].items():
        inv[ing] -= (req_per_one * count)
        if inv[ing] <= 0:
            del inv[ing]

    # Сохраняем состояние инвентаря после списания
    await save_db(message.from_user.id, user)

    # 3. РАСЧЕТ ВРЕМЕНИ
    time_per_unit = recipe.get("time", 10)
    total_wait_time = count * time_per_unit

    # Форматирование времени для сообщения
    if total_wait_time < 60:
        readable_time = f"{total_wait_time} сек."
    else:
        readable_time = f"{total_wait_time // 60} мин. {total_wait_time % 60} сек."

    await message.reply(
        f"⚒️ <b>Крафт запущен!</b>\n\n"
        f"Предмет: {item_emoji} {recipe['name']}\n"
        f"Количество: {count} шт.\n"
        f"Время ожидания: <b>{readable_time}</b>\n\n"
        f"<i>Бот напишет тебе в ЛС о готовности.</i>",
        parse_mode="HTML"
    )

    # 4. ЗАПУСК ФОНОВОГО ТАЙМЕРА
    asyncio.create_task(
        delayed_craft_task(
            message.bot,
            message.from_user.id,
            item_emoji,
            count * recipe.get("amount", 1),
            total_wait_time,
            get_user,
            save_db
        )
    )


# СПИСОК КРАФТОВ
@router.message(F.text.lower() == "крафты")
async def show_crafts_list(message: types.Message):
    text = "⚒️ <b>Список доступных крафтов:</b>\n\n"
    for emoji, data in CRAFT_RECIPES.items():
        ings = ", ".join([f"{count}{e}" for e, count in data["ingredients"].items()])
        text += f"• {emoji} <b>{data['name']}</b> — {ings} ({data.get('time', 10)}с/шт)\n"
    text += "\n<i>Используй: крафт [эмодзи] [кол-во]</i>"
    await message.answer(text, parse_mode="HTML")