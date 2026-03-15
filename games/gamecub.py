import html
import random
import time  # Добавили импорт времени
from aiogram import Router, F, types
from aiogram.filters import Command
from items import GAME_ITEMS

router = Router()

USE_RESPONSES = {
    "🔑": "Ты снял пояс верности и теперь снова можешь дрочить! 🤩",
    "🔰": "Ты потряс значком <b>Летофага</b> 🔰. Приехал 410 автобус и увез тебя в Лагерь Совенок. ",
    "🏳️‍⚧️": "Ты потряс флагом <b>Miside</b> 🏳️‍⚧️. Пришла Мита и превратила тебя в картридж.",
    "🚚": "https://youtu.be/OcX68KbSYD8?si=xpN2flT0ukLnBhOC",
    "📗": [
        "Ты осторожно открываешь <b>📗 Заметки создателя Х: Интересные</b>... (сокращено для краткости)",
        # ... остальные тексты для заметок ...
    ],
    "🎖️": [
        "🎖️ <b>Медаль тестера</b>\n\nТоржественно вручается тестеру по имени <b>{name}</b>...",
        # ... остальные тексты для медали ...
    ]
}

USE_VIDEOS = {
    "🏳️‍⚧️": [
        "BAACAgIAAxkBAAITCWmqsfEDYz4AAUy5uMAcbSCznQhxBwACvY0AAl4qWElS35gDG6jWCzoE",
        "BAACAgIAAxkBAAITHmmqucbBVJqIjOMj435UtnBSiOfyAAIWjgACXipYSXG1uEx8XyMmOgQ",
        "BAACAgIAAxkBAAITIGmque0kDcaFuCBvnfh83jCL2zpbAAIZjgACXipYSVcUCme0RwABjToE",
        "BAACAgIAAxkBAAITImmquiIq3Ri3sTdcClx7YHpuD5PjAAIejgACXipYSR78vNovn3k8OgQ"
    ],
    "🔑": [],  # Сюда можно добавить видео/гифку открытия замка
    "🚛": [
        "BAACAgIAAxkBAAItemm24NkB0J1lw93_eUq4nxjoIPaJAAIcmQAC2ES5SVbnox05RsRiOgQ"
    ],
    "🔰": [
        "BAACAgIAAxkBAAIinmm0m1uLYASs19udNu-x61-zTOYQAAIelwACTkGgSdwKhl8bngsKOgQ",
        "BAACAgIAAxkBAAIiomm0m-pMRBJLiOZU2TngmJcmY5E-AAIflwACTkGgSW8xnLX3hyrGOgQ",
        "BAACAgIAAxkBAAIipGm0nAtS7no4FnONpjcLlS6ABKPwAAIglwACTkGgSe1OaFl8BQHrOgQ",
        "BAACAgIAAxkBAAIipmm0nDF31e7SYjunAAFBNYkcETsCIQACIZcAAk5BoElaQtUXMcHbiToE"
    ]
}


def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        inv = {}
        user["inventory"] = inv
    return inv


async def process_item_use(message: types.Message, item_emoji: str, get_user, save_db):
    if item_emoji == "💦":
        return

    if item_emoji not in GAME_ITEMS:
        return await message.reply("❌ <b>Такого предмета не существует.</b>", parse_mode="HTML")

    user = await get_user(message.from_user.id, message.from_user.username)
    inv_dict = ensure_inv_dict(user)
    chat_id = str(message.chat.id)

    item_count = inv_dict.get(item_emoji, 0)

    if item_count <= 0:
        return await message.reply("❌ <b>У тебя нету такого предмета.</b>", parse_mode="HTML")

    # --- СПЕЦИАЛЬНАЯ ЛОГИКА ДЛЯ ДОЗАТОРА ---
    if item_emoji == "🚰":
        is_active = user.get("spray_dispenser_active", False)

        # Меняем статус на противоположный
        user["spray_dispenser_active"] = not is_active
        await save_db(message.from_user.id, user)

        if not is_active:
            return await message.reply(
                "🚰 <b>Дозатор спрея включен!</b>\nТеперь спреи будут тратиться автоматически при дрочке.",
                parse_mode="HTML")
        else:
            return await message.reply("🚰 <b>Дозатор спрея выключен!</b>", parse_mode="HTML")

    # --- СПЕЦИАЛЬНАЯ ЛОГИКА ДЛЯ КЛЮЧА ---
    if item_emoji == "🔑":
        current_time = time.time()
        belt_expire = user.get("belt_expire_time", 0)

        # Проверяем, надет ли пояс
        if current_time >= belt_expire:
            return await message.reply("❌ <b>На тебе нет пояса верности!</b>", parse_mode="HTML")

        # Снимаем пояс
        user["belt_expire_time"] = 0

        # Сбрасываем КД на дрочку в этом чате (дает снова вздрочнуть)
        if "chats_data" in user and chat_id in user["chats_data"]:
            user["chats_data"][chat_id]["last_droch_time"] = 0

        # Ключ тратится при использовании
        inv_dict["🔑"] -= 1

        await save_db(message.from_user.id, user)
        return await message.reply(USE_RESPONSES["🔑"], parse_mode="HTML")

    # --- СПЕЦИАЛЬНАЯ ЛОГИКА ДЛЯ МЯЧА ---
    if item_emoji == "🏀":
        return await message.reply_dice(emoji="🏀")

    # --- ОБЩАЯ ЛОГИКА ДЛЯ ОСТАЛЬНЫХ ПРЕДМЕТОВ ---
    item_name = GAME_ITEMS[item_emoji].get("name", "Неизвестный предмет")

    # Для остальных предметов трата отключена
    await save_db(message.from_user.id, user)

    response_data = USE_RESPONSES.get(item_emoji)
    if isinstance(response_data, list):
        response_text = random.choice(response_data)
    elif isinstance(response_data, str):
        response_text = response_data
    else:
        response_text = f"✅ Ты успешно использовал <b>{html.escape(item_name)}</b>."

    user_name = html.escape(message.from_user.first_name or "Игрок")
    response_text = response_text.replace("{name}", user_name)

    await message.reply(response_text, parse_mode="HTML")

    video_list = USE_VIDEOS.get(item_emoji)
    if video_list and len(video_list) > 0:
        random_video = random.choice(video_list)
        try:
            await message.reply_video(video=random_video)
        except Exception:
            pass


# --- ОБРАБОТЧИКИ КОМАНД ---

@router.message(Command("use"))
async def cmd_use(message: types.Message, get_user, save_db):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("Укажи предмет. Пример: <code>/use 🔑</code>", parse_mode="HTML")
    await process_item_use(message, args[1].strip(), get_user, save_db)


@router.message(F.text.lower().startswith("юз "))
async def text_use(message: types.Message, get_user, save_db):
    item_emoji = message.text[3:].strip()
    if not item_emoji:
        return await message.reply("Укажи предмет. Пример: <code>юз 🔑</code>", parse_mode="HTML")
    await process_item_use(message, item_emoji, get_user, save_db)


