import random
import html
from aiogram import Router, types, F
from aiogram.filters import Command

router = Router()

# --- RP КОМАНДЫ ---
# Формат: "команда": ["категория1", "категория2", ...]
RP_COMMANDS = {
    "датьврот": ["🍆", "👄", "💦", "🤤", "😳"],
    "лизнуть": ["👅", "💦", "🤤", "😋", "🍆"],
    "поцеловать": ["💋", "😘", "❤️", "🥰", "💕"],
    "шлепнуть": ["👋", "🍑", "😳", "🔥", "💦"],
    "обнять": ["🤗", "❤️", "🥰", "💕", "😊"],
    "кусить": ["🦷", "😈", "💋", "🔥", "😳"],
    "трогать": ["🖐", "😳", "🔥", "💦", "🤤"],
    "кончить": ["💦", "😫", "🍆", "🤤", "😳"],
    "дрочить": ["🍆", "🤚", "💦", "😳", "🔥"],
    "сосать": ["👄", "🍆", "💦", "🤤", "😳"],
    "лизать": ["👅", "💦", "🤤", "😋", "🔥"],
    "трахать": ["🍆", "🍑", "💦", "😫", "🔥"],
    "шлеп": ["👋", "🍑", "😳", "🔥", "💦"],
    "погладить": ["🖐", "😊", "🥰", "😺", "💕"],
    "ударить": ["👊", "😡", "💢", "🤕", "😵"],
    "плюнуть": ["🤮", "💦", "😒", "🤢", "😤"],
    "облизать": ["👅", "💦", "🤤", "😋", "🍆"],
    "в рот": ["🍆", "👄", "💦", "🤤", "😳"],
    "на лицо": ["💦", "😳", "🤤", "👀", "🔥"],
    "дойти": ["😫", "💦", "🔥", "😳", "🤤"],
}

# Ответы бота
RP_RESPONSES = {
    "датьврот": "Ты дал в рот {target}",
    "лизнуть": "Ты лизнул {target}",
    "поцеловать": "Ты поцеловал {target}",
    "шлепнуть": "Ты шлепнул {target} по жопе",
    "обнять": "Ты обнял {target}",
    "кусить": "Ты укусил {target}",
    "трогать": "Ты потрогал {target}",
    "кончить": "Ты кончил на {target}",
    "дрочить": "Ты начал дрочить на {target}",
    "сосать": "Ты начал сосать {target}",
    "лизать": "Ты начал лизать {target}",
    "трахать": "Ты трахаешь {target}",
    "шлеп": "Ты шлепнул {target}",
    "погладить": "Ты погладил {target}",
    "ударить": "Ты ударил {target}",
    "плюнуть": "Ты плюнул в {target}",
    "облизать": "Ты облизал {target}",
    "в рот": "Ты взял {target} в рот",
    "на лицо": "Ты кончил на лицо {target}",
    "дойти": "Ты довёл {target} до пика",
}


@router.message(Command("rp"))
async def cmd_rp_help(message: types.Message):
    """Показывает список всех RP команд"""
    text = "<b>🎭 Список RP команд:</b>\n\n"
    for cmd, emojis in RP_COMMANDS.items():
        text += f"• <code>/rp {cmd}</code> — ответь на сообщение\n"
    text += "\n<i>Используй как ответ на сообщение пользователя</i>"
    await message.reply(text, parse_mode="HTML")


@router.message(Command("датьврот", "лизнуть", "поцеловать", "шлепнуть", "обнять",
                        "кусить", "трогать", "кончить", "дрочить", "сосать",
                        "лизать", "трахать", "шлеп", "погладить", "ударить",
                        "плюнуть", "облизать", "в рот", "на лицо", "дойти"))
async def process_rp_command(message: types.Message):
    """Обрабатывает RP команды"""
    # Проверяем, есть ли ответ на сообщение
    if not message.reply_to_message:
        return await message.reply(
            "❌ <b>Ответь на сообщение пользователя!</b>\n\n"
            "Пример: ответь на сообщение и напиши <code>/датьврот</code>",
            parse_mode="HTML"
        )

    # Получаем целевого пользователя
    target_user = message.reply_to_message.from_user
    target_name = html.escape(target_user.full_name)

    # Получаем команду (без слэша)
    command = message.text.split()[0].replace("/", "").split("@")[0]

    # Проверяем, есть ли такая команда в списке
    if command not in RP_COMMANDS:
        return await message.reply("❌ Неизвестная RP команда.")

    # Выбираем случайные эмодзи (2-3 штуки)
    emojis = RP_COMMANDS[command]
    selected_emojis = "".join(random.sample(emojis, random.randint(2, 3)))

    # Формируем ответ
    response_text = RP_RESPONSES.get(command, f"Ты сделал что-то с {target_name}")
    response_text = response_text.format(target=target_name)

    await message.reply(f"{response_text} {selected_emojis}")


# --- АЛИАСЫ ДЛЯ КОМАНД (чтобы работали без /rp префикса) ---
@router.message(F.text.lower().startswith("дать в рот"))
async def rp_davrot(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["датьврот"], 3))
    await message.reply(f"Ты дал в рот {target} {emojis}")


@router.message(F.text.lower().startswith("лизнуть"))
async def rp_liznut(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["лизнуть"], 3))
    await message.reply(f"Ты лизнул {target} {emojis}")


@router.message(F.text.lower().startswith("поцеловать"))
async def rp_pocelovat(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["поцеловать"], 3))
    await message.reply(f"Ты поцеловал {target} {emojis}")


@router.message(F.text.lower().startswith("шлепнуть"))
async def rp_shlepnut(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["шлепнуть"], 3))
    await message.reply(f"Ты шлепнул {target} по жопе {emojis}")


@router.message(F.text.lower().startswith("обнять"))
async def rp_obnyat(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["обнять"], 3))
    await message.reply(f"Ты обнял {target} {emojis}")


@router.message(F.text.lower().startswith("кусить"))
async def rkusit(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["кусить"], 3))
    await message.reply(f"Ты укусил {target} {emojis}")


@router.message(F.text.lower().startswith("кончить"))
async def rp_konchit(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["кончить"], 3))
    await message.reply(f"Ты кончил на {target} {emojis}")


@router.message(F.text.lower().startswith("дрочить"))
async def rp_drochit(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["дрочить"], 3))
    await message.reply(f"Ты начал дрочить на {target} {emojis}")


@router.message(F.text.lower().startswith("сосать"))
async def rp_sosat(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["сосать"], 3))
    await message.reply(f"Ты начал сосать {target} {emojis}")


@router.message(F.text.lower().startswith("трахать"))
async def rp_trakhat(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["трахать"], 3))
    await message.reply(f"Ты трахаешь {target} {emojis}")


@router.message(F.text.lower().startswith("шлеп"))
async def rp_shlep(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["шлеп"], 3))
    await message.reply(f"Ты шлепнул {target} {emojis}")


@router.message(F.text.lower().startswith("погладить"))
async def rp_gladit(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["погладить"], 3))
    await message.reply(f"Ты погладил {target} {emojis}")


@router.message(F.text.lower().startswith("ударить"))
async def rp_udarit(message: types.Message):
    if not message.reply_to_message:
        return
    target = html.escape(message.reply_to_message.from_user.full_name)
    emojis = "".join(random.sample(RP_COMMANDS["ударить"], 3))
    await message.reply(f"Ты ударил {target} {emojis}")