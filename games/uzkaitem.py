import html
from aiogram import Router, F, types
from aiogram.filters import Command

router = Router()

# 1. СЛОВАРЬ ТЕКСТОВ
# Сюда просто добавляй эмодзи и текст, который должен вывести бот
ITEM_ACTIONS = {
    "💊": "Ты выпил таблетку. Здоровье восстановлено! ❤️",
    "💉": "Ты вколол себе сыворотку. Силы Спермамена наполняют тебя! 💪",
    "🚬": "Ты закурил... Окружающие смотрят с осуждением, но тебе кайфово. 💨",
    "🍎": "Ты съел яблоко. Витамины — это полезно! 🍏",
    "🍺": "Ты выпил кружку пива. Теперь мир кажется чуточку лучше. 🍻",
    "🏳️‍🌈": "Ой... кажется, ты зашел не в ту дверь. 🚪",
    "🧪": "Ты выпил странное семя... Твой голос стал на две октавы выше. 🧬",
    "💰": "ты стал богат",

}

# Интерактивные игры Telegram (кидают кубик/мяч)
GAMES = ["⚽", "🏀", "🎯", "🎳", "🎲", "🎰"]


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


@router.message(F.text.lower().startswith("юз "))
@router.message(Command("use"))
async def handle_use_item(message: types.Message, get_user, save_db):
    user_id = message.from_user.id

    # Парсим эмодзи
    if message.text.startswith("/use"):
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("❌ Напиши: `/use [эмодзи]`")
        item_emoji = args[1]
    else:
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            return await message.reply("⚠️ Напиши: `юз [эмодзи]`")
        item_emoji = parts[1].strip()

    # База данных
    user = await get_user(user_id)
    inv = ensure_inv_dict(user)

    # Проверка наличия
    if item_emoji not in inv or inv[item_emoji] <= 0:
        return await message.reply(f"❌ У тебя нет <code>{item_emoji}</code>!", parse_mode="HTML")

    # Списание предмета
    inv[item_emoji] -= 1
    if inv[item_emoji] <= 0:
        del inv[item_emoji]

    user["inventory"] = inv
    await save_db(user_id, user)

    # --- ЛОГИКА ВЫВОДА ---

    # 1. Проверка на Игры (Dice)
    if item_emoji in GAMES:
        return await message.answer_dice(emoji=item_emoji)

    # 2. Поиск текста в словаре
    custom_text = ITEM_ACTIONS.get(item_emoji)

    if custom_text:
        # Если текст найден в словаре ITEM_ACTIONS
        await message.reply(custom_text)
    else:
        # Если текста нет в словаре (стандартный ответ)
        await message.reply(f"✅ Ты использовал <code>{item_emoji}</code>!", parse_mode="HTML")

        # --- ЛОГИКА ВЫВОДА ---

        # 1. Сначала проверяем на игры (Dice)
        if item_emoji in GAMES:
            return await message.answer_dice(emoji=item_emoji)

        # 2. СПЕЦ-ЛОГИКА ДЛЯ ЧЕМОДАНА 💼
        if item_emoji == "💼":
            user["hide_coins"] = True  # Ставим флаг в данные юзера
            await save_db(user_id, user)
            return await message.reply(
                "💼 Ты упаковал свои ФармКоины в чемодан! Теперь их не будет видно в профиле и инвентаре (но платить ими всё еще можно).")

        # 3. Поиск обычного текста в словаре
        custom_text = ITEM_ACTIONS.get(item_emoji)
        if custom_text:
            await message.reply(custom_text)
        else:
            await message.reply(f"✅ Ты использовал <code>{item_emoji}</code>!", parse_mode="HTML")