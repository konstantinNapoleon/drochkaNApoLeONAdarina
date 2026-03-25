import html
import random
import time
from datetime import datetime, timezone, timedelta
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from items import GAME_ITEMS

router = Router()

# СТИКЕРЫ
POPPIT_STICKERS = ["CAACAgIAAxkBAAEQxE1puHx0R6iBBX-FirEhnYj38TLOFQACMg4AAm1c0Ei6RlcE9wmVFToE"]
CAT_STICKER_ID = ["CAACAgIAAxkBAAEQxkZpunAQzNfxqeo7ZHe8vEzqVJT7ZAACrRIAAiHm6ErMPS5b666L7ToE"]
MUTE_STICKER = "CAACAgIAAxkBAAEQy2ZpvnCswPfY_0Kf45HGsFICi0I5uAACAQwAAt4zwEt7E1Fhuh-zuzoE"

# Список предметов Pop It
POPPIT_ITEMS = ["🔴", "🟢", "🟪", "🟠", "🟡", "🔵", "🟣", "💜"]

USE_RESPONSES = {
    "🔑": "Ты снял пояс верности и теперь снова можешь дрочить! 🤩",
    "💉": "Тестостерон резко прилил к херу и ты можешь дрочить! 💪",
    "🛌": "Тссс... Ты спрятался от мамки и можешь дрочить! 👌",
    "📕": "Ты полистал журнал FamHub и грусть как рукой сняло! 📕✨",
    "🚛": "Ты сел в рейс с дядей Федором. Гони, гони, быстрее.",
    "🔰": "Ты потряс значком <b>Летофага</b> 🔰. Приехал 410 автобус и увез тебя в Лагерь Совенок. ",
    "🏴‍☠️": "Ты потряс флагом <b>Карибского моря</b> 🏴‍☠️. Приплыл Джек Воробей.",
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


async def process_item_use(message: types.Message, item_emoji: str, get_user, save_db):
    if item_emoji == "💦": return

    if item_emoji not in GAME_ITEMS:
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

    # --- КИРПИЧ (🧱) ---
    if item_emoji == "🧱":
        if not message.reply_to_message:
            return await message.reply(
                "Чтобы использовать 🧱 <b>Кирпич</b>, нужно ответить на сообщение того, кого ты хочешь ебнуть!",
                parse_mode="HTML")

        target_user_obj = message.reply_to_message.from_user
        if target_user_obj.id == message.from_user.id:
            return await message.reply("Зачем ты бьешь себя? Остановись! 🧱")

        # Получаем данные цели
        target_data = await get_user(target_user_obj.id, target_user_obj.username)
        target_inv = ensure_inv_dict(target_data)
        target_name = html.escape(target_user_obj.full_name)

        # 1. ПРОВЕРКА ЩИТА (🛡) - Многоразовый с КД
        if target_inv.get("🛡", 0) > 0:
            last_shield_use = target_data.get("last_shield_block_time", 0)
            if current_time - last_shield_use >= 600:  # 10 минут
                target_data["last_shield_block_time"] = current_time
                inv_dict["🧱"] -= 1
                await save_db(message.from_user.id, user)
                await save_db(target_user_obj.id, target_data)
                return await message.answer(
                    f"🛡 <b>{target_name}</b> отразил твой кирпич <b>Щитом великого дрочуна</b>! Ебнуть не получилось.",
                    parse_mode="HTML")

        # 2. ПРОВЕРКА КАСКИ (🪖) - Одноразовая, защита работает пока есть в инвентаре
        if target_inv.get("🪖", 0) > 0 and target_data.get("helmet_active"):
            target_inv["🪖"] -= 1  # Каска ломается
            # Если каски закончились, выключаем статус активной защиты
            if target_inv["🪖"] <= 0:
                target_data["helmet_active"] = False

            inv_dict["🧱"] -= 1  # Кирпич тратится
            await save_db(message.from_user.id, user)
            await save_db(target_user_obj.id, target_data)
            return await message.answer(
                f"🪖 <b>{target_name}</b> выжил после удара кирпичом, но его <b>Каска</b> разлетелась в щепки! Минус кирпич и минус каска. 😳",
                parse_mode="HTML")

        # 3. ЕСЛИ НЕТ ЗАЩИТЫ - МУТ
        try:
            until_date = datetime.now() + timedelta(minutes=10)
            await message.chat.restrict(
                user_id=target_user_obj.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            inv_dict["🧱"] -= 1
            await save_db(message.from_user.id, user)
            await message.answer(f"Ты ебнул <b>{target_name}</b> 🧱. Он замолчал на 10 минут.", parse_mode="HTML")
            return await message.answer_sticker(sticker=MUTE_STICKER)
        except Exception:
            return await message.reply(
                "❌ <b>Ошибка!</b>\nЛибо я не админ, либо ты пытаешься ударить кирпичом того, кто в каске (админа).",
                parse_mode="HTML")

    # --- КАСКА (🪖) ВКЛЮЧЕНИЕ/ВЫКЛЮЧЕНИЕ ---
    if item_emoji == "🪖":
        is_active = user.get("helmet_active", False)
        # Запрещаем включать, если касок нет
        if not is_active and inv_dict.get("🪖", 0) <= 0:
            return await message.reply("❌ У тебя нет касок в инвентаре, чтобы их включить! 🪖", parse_mode="HTML")

        user["helmet_active"] = not is_active
        await save_db(message.from_user.id, user)
        status = "включена" if not is_active else "выключена"
        return await message.reply(
            f"🪖 <b>Каска {status}!</b>\nТеперь она будет автоматически защищать тебя, пока каски не закончатся.",
            parse_mode="HTML")

    # --- ЩИТ (🛡) Инфо ---
    if item_emoji == "🛡":
        return await message.reply(
            "🛡 <b>Щит великого дрочуна</b> работает автоматически. Он защитит тебя от кирпича раз в 10 минут, если лежит в инвентаре.",
            parse_mode="HTML")

    # --- ПРОВЕРКА СОСТОЯНИЯ ПЕРЕД ИСПОЛЬЗОВАНИЕМ ---
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

    # --- УСПЕШНОЕ ПРИМЕНЕНИЕ (💉, 🛌, 📕, 🔑) ---
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
            rem = int((600 - (current_time - last_use)) / 60)
            sec = int((600 - (current_time - last_use)) % 60)
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
        status = "включен" if not is_active else "выключена"
        return await message.reply(
            f"🚰 <b>Дозатор спрея {status}!</b>\nТеперь спреи будут тратиться автоматически при дрочке.",
            parse_mode="HTML")

    # --- НОВОЕ: ЛУПЫ (🔎 и 🔍) ---
    if item_emoji in ["🔎", "🔍"]:
        bonus = 100 if item_emoji == "🔎" else 1000
        # Базовая инициализация, если размера нет
        if "penis_size" not in user:
            user["penis_size"] = 10

        user["penis_size"] += bonus
        inv_dict[item_emoji] -= 1

        item_name = GAME_ITEMS[item_emoji].get("name", "Лупа")
        await save_db(message.from_user.id, user)
        return await message.reply(
            f"🔸 Ты успешно применил {item_emoji} <b>{item_name}</b>. Твой хуй стал больше на <b>{bonus} см</b>.\n"
            f"❤️‍🔥 Новый размер — <b>{user['penis_size']} см</b>.",
            parse_mode="HTML"
        )

    # --- ЛОГИКА СИНЕЙ КНИГИ (БЕЗ ТРАТЫ ПРЕДМЕТА) ---
    if item_emoji == "📘":
        craft_text = (
            "<b>Список доступных крафтов ✨</b>\n\n"
            "• 🚬 <b>Сигарета</b> — 1 📜 + 1 🍃\n"
            "• 🏚️ <b>Халупа</b> — 50 🧱 + 3 🌫\n"
            "• 🏠 <b>Дом</b> — 200 🧱 + 6 🌫\n"
            "• 🏰 <b>Крепость</b> — 1000 🧱 + 10 🌫\n\n"
            "<i>Ингредиенты можно найти в каталоге</i>"
        )
        return await message.reply(craft_text, parse_mode="HTML")

    # --- МЯЧ (🏀) ---
    if item_emoji == "🏀":
        return await message.reply_dice(emoji="🏀")

    # --- ОБЩАЯ ЛОГИКА ДЛЯ ОСТАЛЬНЫХ (Машины, Флаги, Книги) ---
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

    # Отправка видео, если оно есть
    video_list = USE_VIDEOS.get(item_emoji)
    if video_list and len(video_list) > 0:
        random_video = random.choice(video_list)
        try:
            await message.reply_video(video=random_video)
        except Exception:
            pass


@router.message(Command("use"))
async def cmd_use(message: types.Message, get_user, save_db):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("Укажи предмет. Пример: <code>/use 🔑</code>", parse_mode="HTML")
    await process_item_use(message, args[1].strip(), get_user, save_db)


@router.message(F.text.lower().startswith("юз "))
async def text_use(message: types.Message, get_user, save_db):
    item_emoji = message.text[3:].strip()
    if not item_emoji: return
    await process_item_use(message, item_emoji, get_user, save_db)


