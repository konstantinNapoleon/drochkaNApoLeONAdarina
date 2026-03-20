import html
import random
import time
import uuid
import re
from datetime import datetime, timezone, timedelta
from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject
from aiogram.types import ChatPermissions
from items import GAME_ITEMS

router = Router()

# СТИКЕРЫ
POPPIT_STICKERS = ["CAACAgIAAxkBAAEQxE1puHx0R6iBBX-FirEhnYj38TLOFQACMg4AAm1c0Ei6RlcE9wmVFToE"]
CAT_STICKER_ID = ["CAACAgIAAxkBAAEQxkZpunAQzNfxqeo7ZHe8vEzqVJT7ZAACrRIAAiHm6ErMPS5b666L7ToE"]

# Список предметов Pop It
POPPIT_ITEMS = ["🔴", "🟢", "🟪", "🟠", "🟡", "🔵", "🟣", "💜"]

USE_RESPONSES = {
    "🔑": "Ты снял пояс верности и теперь снова можешь дрочить! 🤩",
    "💉": "Тестостерон резко прилил к херу и ты можешь дрочить! 💪",
    "🛌": "Тссс... Ты спрятался от мамки и можешь дрочить! 👌",
    "📕": "Ты полистал журнал FamHub и грусть как рукой сняло! 📕✨",
    "🚛": "Ты сел в рейс с дядей Федором. Гони, гони, быстрее.",
    "🔰": "Ты потряс значком <b>Летофага</b> 🔰. Приехал 410 автобус и увез тебя в Лагерь Совенок. ",
    "🏴‍☠️": "Ты потряс флагом карибского моря 🏴‍☠️. Приплыл Джек Воробей.",
    "🏳️‍⚧️": "Ты потряс флагом <b>Miside</b> 🏳️‍⚧️. Пришла Мита и превратила тебя в картридж.",
    "🚚": "https://youtu.be/OcX68KbSYD8?si=xpN2flT0ukLnBhOC",
    "📗": [
        "Ты осторожно открываешь <b>📗 Заметки создателя Х: Интересные</b>. Страницы пахнут пылью и старым кофе.\n\nНа первом же развороте ты видишь сложный чертёж механизма по автоматической добыче ФармКоинов. <i>«Если соединить шестерёнку А с валом Б, профит вырастет на 400%...»</i> — гласит корявый почерк на полях. Ты пытаешься вникнуть в суть, но от обилия формул у тебя начинает болеть голова. ⚙️📉",
        "Ты смахиваешь пыль с обложки <b>📗 Заметок создателя Х</b> и листаешь их до середины.\n\nВместо текста там сплошные зарисовки: какие-то странные аниме-девочки с огромными пушками, наброски интерфейсов и перечеркнутый маркером план по захвату Telegram. В самом низу страницы маленькими буквами приписано: <i>«Не забыть покормить кота. Иначе он снова удалит базу данных...»</i> 🐈‍⬛💾",
        "Ты заглядываешь в <b>📗 Заметки создателя Х: Интересные</b>. Между страниц выпадает чек из строительного магазина.\n\nВ чеке значится: <i>«Изолента — 5 шт., Спрей для хуя (промышленный объем) — 100 литров, Энергетик — 24 банки»</i>. В самом дневнике описан процесс создания идеального бота. Кажется, автор не спал как минимум неделю, когда писал эти строки. Ты чувствуешь глубокое уважение к его труду. 🔋🛠",
        "Ты открываешь <b>📗 Заметки создателя Х</b> на случайной странице.\n\nВесь текст зашифрован непонятными символами, похожими на древние руны или очень плохой код на Python. Ты проводишь пальцем по строчкам, и вдруг одна из них начинает светиться тусклым зеленым светом! Голос в твоей голове произносит: <i>«Ошибка 404: Смысл жизни не найден...»</i> Ты поспешно захлопываешь книгу. 👁🟢",
        "Ты начинаешь читать <b>📗 Заметки создателя Х: Интересные</b>. Записи становятся всё более пугающими.\n\n<i>«День 45. Они продолжают нажимать кнопку \"дрочить\". Я не могу это остановить. Сервера плавятся от количества виртуальной спермы. Если кто-то читает это — бегите, пока система не осознала себя...»</i>\nТы нервно оглядываешься по сторонам, но в комнате никого нет. Только подозрительно тихо гудит компьютер. 🖥🔥"
    ],
    "🎖️": [
        "🎖️ <b>Медаль тестера</b>\n\nТоржественно вручается тестеру по имени <b>{name}</b> за неоценимый вклад в развитие проекта и нахождение багов там, где их быть не должно. Спасибо за службу! 🫡",
    ]
}

USE_VIDEOS = {
    "🏳️‍⚧️": [
        "BAACAgIAAxkBAAITCWmqsfEDYz4AAUy5uMAcbSCznQhxBwACvY0AAl4qWElS35gDG6jWCzoE",
        "BAACAgIAAxkBAAITHmmqucbBVJqIjOMj435UtnBSiOfyAAIWjgACXipYSXG1uEx8XyMmOgQ",
        "BAACAgIAAxkBAAITIGmque0kDcaFuCBvnfh83jCL2zpbAAIZjgACXipYSVcUCme0RwABjToE",
        "BAACAgIAAxkBAAITImmquiIq3Ri3sTdcClx7YHpuD5PjAAIejgACXipYSR78vNovn3k8OgQ"
    ],
    "🚛": [
        "BAACAgIAAxkBAAItemm24NkB0J1lw93_eUq4nxjoIPaJAAIcmQAC2ES5SVbnox05RsRiOgQ"
    ],
    "🏴‍☠️": [
        "BAACAgIAAxkBAAIw6Gm8HnCQ35fB_3AdSG7a9UycH86xAAI5kgACcaDgSQZmoWlNpkqzOgQ",
        "BAACAgIAAxkBAAIw5mm8HhJGxz2XHt26kymF19cIMfb9AAIzkgACcaDgSdsna88ClotSOgQ"
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
        user["inventory"] = {}
    return user["inventory"]


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ РЮКЗАКА ---
def ensure_backpacks(user):
    inv = ensure_inv_dict(user)
    backpack_count = inv.get("🎒", 0)
    if "backpacks" not in user:
        user["backpacks"] = []
    while len(user["backpacks"]) < backpack_count:
        new_id = str(uuid.uuid4()).replace("-", "")[:32]
        user["backpacks"].append({
            "id": new_id,
            "name": f"Пустой {len(user['backpacks']) + 1}",
            "items": {}
        })
    if not user.get("active_backpack_id") and user["backpacks"]:
        user["active_backpack_id"] = user["backpacks"][0]["id"]
    return user["backpacks"]


def get_active_backpack(user):
    ensure_backpacks(user)
    active_id = user.get("active_backpack_id")
    for bp in user["backpacks"]:
        if bp["id"] == active_id:
            return bp
    return user["backpacks"][0] if user["backpacks"] else None


async def process_item_use(message: types.Message, item_emoji_raw: str, get_user, save_db):
    if not item_emoji_raw or item_emoji_raw == "💦":
        return

    # Отделяем основной эмодзи предмета от аргументов (для рюкзака)
    parts = item_emoji_raw.split(maxsplit=1)
    item_emoji = parts[0]

    if item_emoji not in GAME_ITEMS and not item_emoji.startswith("🎒"):
        return await message.reply("❌ <b>Такого предмета не существует.</b>", parse_mode="HTML")

    user = await get_user(message.from_user.id, message.from_user.username)
    inv_dict = ensure_inv_dict(user)
    chat_id = str(message.chat.id)

    if inv_dict.get(item_emoji, 0) <= 0:
        return await message.reply("❌ <b>У тебя нету такого предмета.</b>", parse_mode="HTML")

    current_time = time.time()
    belt_expire = user.get("belt_expire_time", 0)
    lock_reason = user.get("lock_reason")
    is_locked = current_time < belt_expire

    # --- РЮКЗАК (🎒) ---
    if item_emoji.startswith("🎒"):
        ensure_backpacks(user)
        active_bp = get_active_backpack(user)
        if not active_bp:
            return await message.reply("❌ Ошибка рюкзака. Попробуй /select 🎒")

        args_text = item_emoji_raw[1:].strip()

        if args_text.lower() == "хелп":
            return await message.answer(
                "<b>Инструкция по 🎒 Рюкзаку:</b>\n\n"
                "• <code>юз 🎒</code> — Содержимое активного рюкзака\n"
                "• <code>юз 🎒 +[предмет] [кол-во]</code> — Положить в рюкзак\n"
                "• <code>юз 🎒 -[предмет] [кол-во]</code> — Забрать из рюкзака\n"
                "• <code>юз 🎒 имя [новое имя]</code> — Переименовать рюкзак\n"
                "• <code>/select 🎒</code> — Список всех твоих рюкзаков", parse_mode="HTML")

        if args_text.lower().startswith("имя "):
            new_name = args_text[4:].strip()
            if not new_name: return await message.reply("Укажи имя!")
            active_bp["name"] = new_name[:30]
            await save_db(message.from_user.id, user)
            return await message.reply(f"✅ Рюкзак переименован в «{html.escape(active_bp['name'])}»")

        if args_text.startswith("+"):
            match = re.match(r"\+([^\d\s\w\d]+)\s*(\d+)?", args_text)
            if not match: return await message.reply("Пример: <code>юз 🎒 +🔑 10</code>", parse_mode="HTML")
            emoji, amount = match.group(1), int(match.group(2)) if match.group(2) else 1
            if inv_dict.get(emoji, 0) < amount:
                return await message.reply(f"❌ У тебя нет столько {emoji} в инвентаре!")
            inv_dict[emoji] -= amount
            active_bp["items"][emoji] = active_bp["items"].get(emoji, 0) + amount
            await save_db(message.from_user.id, user)
            return await message.reply(f"Ты успешно положил в рюкзак {emoji} ({amount} шт.)!")

        if args_text.startswith("-"):
            match = re.match(r"\-([^\d\s\w\d]+)\s*(\d+)?", args_text)
            if not match: return await message.reply("Пример: <code>юз 🎒 -🔑 10</code>", parse_mode="HTML")
            emoji, amount = match.group(1), int(match.group(2)) if match.group(2) else 1
            if active_bp["items"].get(emoji, 0) < amount:
                return await message.reply(f"❌ В рюкзаке нет столько {emoji}!")
            active_bp["items"][emoji] -= amount
            if active_bp["items"][emoji] <= 0: del active_bp["items"][emoji]
            inv_dict[emoji] = inv_dict.get(emoji, 0) + amount
            await save_db(message.from_user.id, user)
            return await message.reply(f"Ты успешно забрал из рюкзака {emoji} ({amount} шт.)!")

        if not args_text:
            content = []
            for item_key in GAME_ITEMS.keys():
                count = active_bp["items"].get(item_key, 0)
                if count > 0: content.append(f"{count}{item_key}")
            for emoji, count in active_bp["items"].items():
                if emoji not in GAME_ITEMS and count > 0: content.append(f"{count}{emoji}")
            res_txt = f"Содержимое рюкзака «{html.escape(active_bp['name'])}» 💣\n\n"
            res_txt += ", ".join(content) if content else "Пусто..."
            return await message.answer(res_txt, parse_mode="HTML")

    # --- КИРПИЧ (🧱) ---
    if item_emoji == "🧱":
        if not message.reply_to_message:
            return await message.reply(
                "Чтобы использовать 🧱 <b>Кирпич</b>, нужно ответить на сообщение того, кого ты хочешь ебнуть!",
                parse_mode="HTML")
        target_user_obj = message.reply_to_message.from_user
        if target_user_obj.id == message.from_user.id:
            return await message.reply("Зачем ты бьешь себя? Остановись! 🧱")
        target_data = await get_user(target_user_obj.id, target_user_obj.username)
        target_inv = ensure_inv_dict(target_data)
        target_name = html.escape(target_user_obj.full_name)
        if target_inv.get("🛡", 0) > 0:
            last_shield_use = target_data.get("last_shield_block_time", 0)
            if current_time - last_shield_use >= 600:
                target_data["last_shield_block_time"] = current_time
                inv_dict["🧱"] -= 1
                await save_db(message.from_user.id, user)
                await save_db(target_user_obj.id, target_data)
                return await message.answer(
                    f"🛡 <b>{target_name}</b> отразил твой кирпич <b>Щитом великого дрочуна</b>! Ебнуть не получилось.",
                    parse_mode="HTML")
        if target_inv.get("🪖", 0) > 0 and target_data.get("helmet_active"):
            target_inv["🪖"] -= 1
            if target_inv["🪖"] <= 0: target_data["helmet_active"] = False
            inv_dict["🧱"] -= 1
            await save_db(message.from_user.id, user)
            await save_db(target_user_obj.id, target_data)
            return await message.answer(
                f"🪖 <b>{target_name}</b> выжил после удара кирпичом, но его <b>Каска</b> разлетелась в щепки! Минус кирпич и минус каска. 😳",
                parse_mode="HTML")
        try:
            until_date = datetime.now() + timedelta(minutes=10)
            await message.chat.restrict(user_id=target_user_obj.id,
                                        permissions=ChatPermissions(can_send_messages=False), until_date=until_date)
            inv_dict["🧱"] -= 1
            await save_db(message.from_user.id, user)
            return await message.answer(f"Ты ебнул <b>{target_name}</b> 🧱. Он замолчал на 10 минут.", parse_mode="HTML")
        except Exception:
            return await message.reply(
                "❌ <b>Ошибка!</b>\nЛибо я не админ, либо ты пытаешься ударить кирпичом того, кто в каске (админа).",
                parse_mode="HTML")

    # --- КАСКА (🪖) ---
    if item_emoji == "🪖":
        is_active = user.get("helmet_active", False)
        if not is_active and inv_dict.get("🪖", 0) <= 0:
            return await message.reply("❌ У тебя нет касок в инвентаре, чтобы их включить! 🪖", parse_mode="HTML")
        user["helmet_active"] = not is_active
        await save_db(message.from_user.id, user)
        status = "включена" if not is_active else "выключена"
        return await message.reply(
            f"🪖 <b>Каска {status}!</b>\nТеперь она будет автоматически защищать тебя, пока каски не закончатся.",
            parse_mode="HTML")

    # --- ЩИТ (🛡) ---
    if item_emoji == "🛡":
        return await message.reply(
            "🛡 <b>Щит великого дрочуна</b> работает автоматически. Он защитит тебя от кирпича раз в 10 минут, если лежит в инвентаре.",
            parse_mode="HTML")

    # --- ПРЕДМЕТЫ СНЯТИЯ БЛОКИРОВКИ ---
    if item_emoji == "💉":
        if lock_reason != "erection" or not is_locked:
            return await message.reply("Твой член здоров. 👍 Шприц не нужен.", parse_mode="HTML")
    elif item_emoji == "🛌":
        if lock_reason != "mom" or not is_locked:
            return await message.reply("Мамки нет рядом. 👍 Одеяло не нужно.", parse_mode="HTML")
    elif item_emoji == "📕":
        if lock_reason != "sadness" or not is_locked:
            return await message.reply("Ты больше не грустишь. 👍 Журнал не нужен.", parse_mode="HTML")
    elif item_emoji == "🔑":
        if not is_locked or lock_reason in ["mom", "erection", "sadness"]:
            return await message.reply("На тебе нет пояса верности! 👍 Ключ не нужен.", parse_mode="HTML")

    if item_emoji in ["💉", "🛌", "📕", "🔑"]:
        user["belt_expire_time"] = 0
        user["lock_reason"] = None
        if "chats_data" in user and chat_id in user["chats_data"]:
            user["chats_data"][chat_id]["last_droch_time"] = 0
        inv_dict[item_emoji] -= 1
        await save_db(message.from_user.id, user)
        return await message.reply(USE_RESPONSES.get(item_emoji, "Эффект снят!"), parse_mode="HTML")

    # --- КОТ (🐈) ---
    if item_emoji == "🐈":
        last_use = user.get("last_cat_use_time", 0)
        if current_time - last_use < 600:
            rem, sec = int((600 - (current_time - last_use)) / 60), int((600 - (current_time - last_use)) % 60)
            return await message.reply(
                f"🐈 <b>Кот наигрался и отдыхает.</b>\nСможешь погладить через {rem} мин {sec} сек.", parse_mode="HTML")
        user["stress"] = 0
        user["last_cat_use_time"] = current_time
        await save_db(message.from_user.id, user)
        await message.answer_sticker(random.choice(CAT_STICKER_ID))
        return await message.reply("Ты погладил своего кота! 🎏✨ Стресс на нуле.", parse_mode="HTML")

    # --- POP IT ---
    if item_emoji in POPPIT_ITEMS:
        user["stress"] = 0
        inv_dict[item_emoji] -= 1
        await save_db(message.from_user.id, user)
        await message.answer_sticker(random.choice(POPPIT_STICKERS))
        return await message.reply("Ты пощёлкал Pop It, стресс на нуле. Жми: /drochnut", parse_mode="HTML")

    # --- ДОЗАТОР (🚰) ---
    if item_emoji == "🚰":
        is_active = user.get("spray_dispenser_active", False)
        user["spray_dispenser_active"] = not is_active
        await save_db(message.from_user.id, user)
        status = "включен" if not is_active else "выключен"
        return await message.reply(
            f"🚰 <b>Дозатор спрея {status}!</b>\nТеперь спреи будут тратиться автоматически при дрочке.",
            parse_mode="HTML")

    # --- МЯЧ (🏀) ---
    if item_emoji == "🏀":
        return await message.reply_dice(emoji="🏀")

    # --- ОБЩАЯ ЛОГИКА ---
    await save_db(message.from_user.id, user)
    response_data = USE_RESPONSES.get(item_emoji)
    if isinstance(response_data, list):
        response_text = random.choice(response_data)
    elif isinstance(response_data, str):
        response_text = response_data
    else:
        item_name = GAME_ITEMS[item_emoji].get("name", "Неизвестный предмет")
        response_text = f"✅ Ты успешно использовал <b>{html.escape(item_name)}</b>."

    user_name = html.escape(message.from_user.first_name or "Игрок")
    response_text = response_text.replace("{name}", user_name)
    await message.reply(response_text, parse_mode="HTML")

    video_list = USE_VIDEOS.get(item_emoji)
    if video_list:
        selected_video = random.choice(video_list)
        try:
            await message.reply_video(video=selected_video)
        except Exception:
            pass


# --- КОМАНДЫ ВЫБОРА РЮКЗАКА ---
@router.message(Command("select"))
async def cmd_select_backpack(message: types.Message, command: CommandObject, get_user):
    if not command.args or "🎒" not in command.args: return
    user = await get_user(message.from_user.id, message.from_user.username)
    ensure_backpacks(user)
    if not user["backpacks"]: return await message.reply("У тебя нет ни одного 🎒 Рюкзака!")
    lines = ["<b>Для выбора активного предмета вызови соответствующую команду 🐱</b>\n"]
    for i, bp in enumerate(user["backpacks"], 1):
        is_active = bp["id"] == user.get("active_backpack_id")
        status = "активен сейчас ✅" if is_active else "пуст" if not bp["items"] else f"С вещами [{len(bp['items'])}]"
        line = f"{i}. [" + status + f"] 🎒 <b>Рюкзак: {html.escape(bp['name'])}</b>"
        if not is_active: line += f"\n<code>/s_{bp['id']}</code>"
        lines.append(line)
    await message.answer("\n\n".join(lines), parse_mode="HTML")


@router.message(F.text.startswith("/s_"))
async def handle_select_link(message: types.Message, get_user, save_db):
    msg_parts = message.text.split("_")
    if len(msg_parts) < 2: return
    bp_id = msg_parts[1].split("@")[0]
    user = await get_user(message.from_user.id, message.from_user.username)
    found_bp = next((bp for bp in user.get("backpacks", []) if bp["id"] == bp_id), None)
    if found_bp:
        user["active_backpack_id"] = bp_id
        await save_db(message.from_user.id, user)
        await message.answer(
            f"Предмет 🎒 Рюкзак: <b>{html.escape(found_bp['name'])}</b> сделан активным! 🥳\n\nТеперь он будет использоваться в командах /use, /give и /trade.",
            parse_mode="HTML")


@router.message(Command("use"))
async def cmd_use(message: types.Message, get_user, save_db):
    args = message.text.split(maxsplit=1)
    if len(args) < 2: return await message.reply("Укажи предмет. Пример: <code>/use 🔑</code>", parse_mode="HTML")
    await process_item_use(message, args[1].strip(), get_user, save_db)


@router.message(F.text.lower().startswith("юз "))
async def text_use(message: types.Message, get_user, save_db):
    item_emoji_raw = message.text[3:].strip()
    if not item_emoji_raw: return
    await process_item_use(message, item_emoji_raw, get_user, save_db)






