import random
import time
import html
import datetime
from aiogram import Router, types, F
from aiogram.filters import Command

# Импортируем твой основной словарь предметов
from items import GAME_ITEMS

router = Router()

FARMCOIN = "💰"
# Юзернейм чата, где разрешен поиск (без @)
ALLOWED_CHAT = "factory_droch_bot"

# --- СПИСОК ЭМОДЗИ ДЛЯ ЗАВОДА (17 шт) ---
FACTORY_LOOT_POOL = [
    "🔧", "🔩", "⚙️", "📻", "🔋", "📦", "🪑", "🛢️", "🧱",
    "🧺", "🔨", "🧹", "🏺", "📀", "☎️", "📺", "🧥", "🍃", "📜"
]

# --- СПИСОК КРЕАТИВНЫХ ОПИСАНИЙ (УСПЕХ) ---
SEARCH_TEXTS = [
    "Пробираясь сквозь груды мусора и пыльные цеха, ты замечаешь что-то ценное...",
    "Разгребая старые завалы в углу сборочного цеха, твои глаза зацепились за это...",
    "Пнув ногой заржавевшую бочку, ты услышал странный звон. Оказалось, это...",
    "В тени огромного станка, покрытого паутиной, тебе удалось отыскать...",
    "Среди битого кирпича и старой проводки блеснуло нечто интересное..."
]

# --- СПИСОК КРЕАТИВНЫХ ОПИСАНИЙ (НЕУДАЧА) ---
FAIL_TEXTS = [
    "Ты битый час бродил по пустым цехам, но нашел только вековую пыль и сквозняк.",
    "Издалека послышался лай собак и свет фонарей охраны. Тебе пришлось затаиться и уйти ни с чем.",
    "Все ящики в этом секторе оказались абсолютно пустыми. Видимо, кто-то обыскал их до тебя."
    "Ты подумал о маме и папе что они остались одни дома и вернулся назад."
]

# --- ЛОГИКА РЫНКА (5 случайных предметов) ---
market_prices = {}
next_market_update = 0


def update_market():
    global market_prices, next_market_update
    now = time.time()
    if now >= next_market_update:
        # Выбираем 5 случайных предметов из 17 возможных
        selected_items = random.sample(FACTORY_LOOT_POOL, 5)
        market_prices = {item: random.randint(10, 200) for item in selected_items}
        next_market_update = now + 3600


def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        if isinstance(inv, list):
            new_inv = {}
            for item in inv: new_inv[item] = new_inv.get(item, 0) + 1
            user["inventory"] = new_inv
        else:
            user["inventory"] = {}
    return user["inventory"]


# --- КОМАНДА /search (Четные/Нечетные по МСК) ---
@router.message(Command("search"))
async def cmd_search(message: types.Message, get_user, save_db):
    if message.chat.username != ALLOWED_CHAT:
        return await message.reply(f"❌ ЧУУУВАААК искать хлам можно только в чате @{ALLOWED_CHAT}!")

    # Время МСК (UTC+3)
    current_hour = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)).hour
    is_even = current_hour % 2 == 0

    success = True
    if not is_even:
        if random.random() > 0.10:  # 10% шанс в нечетный час
            success = False

    if not success:
        fail_desc = random.choice(FAIL_TEXTS)
        text = (
            "╭ 🏭 <b>ПОИСК...</b>\n"
            "│\n"
            f"╰ {fail_desc}\n\n"
            "👣 <i>К сожалению, твой мешок остался совершенно пустым...</i>"
        )
        return await message.reply(text, parse_mode="HTML")

    user = await get_user(message.from_user.id, message.from_user.username)
    inv = ensure_inv_dict(user)

    found = {}
    item1 = random.choice(FACTORY_LOOT_POOL)
    count1 = random.randint(1, 4)
    found[item1] = count1

    is_lucky = False
    if random.random() < 0.09:
        is_lucky = True
        item2 = random.choice(FACTORY_LOOT_POOL)
        found[item2] = found.get(item2, 0) + random.randint(1, 4)

    for it, cnt in found.items():
        inv[it] = inv.get(it, 0) + cnt
    await save_db(message.from_user.id, user)

    description = random.choice(SEARCH_TEXTS)
    text = (
        "╭ 🏭 <b>ПОИСК...</b>\n"
        "│\n"
        f"╰ {description}\n\n"
    )

    for it, cnt in found.items():
        item_data = GAME_ITEMS.get(it, {})
        name = item_data.get("name", "Неизвестный хлам")
        text += f"📦 {it} <b>{name}</b> (+{cnt})\n"

    if is_lucky:
        text += "\n🍀 <b>ебать! Тебе повезло найти двойную добычу!</b>"

    await message.reply(text, parse_mode="HTML")


# --- КОМАНДА /lom ---
@router.message(Command("lom"))
async def cmd_lom(message: types.Message, get_user):
    user = await get_user(message.from_user.id, message.from_user.username)
    inv = ensure_inv_dict(user)
    items_in_inv = {k: v for k, v in inv.items() if k in FACTORY_LOOT_POOL and v > 0}

    if not items_in_inv:
        return await message.reply("📦 Чел у тебя нет хлама. иди на завод: /search")

    text = "🛠 <b>Твой мешок с хламом:</b>\n\n"
    for emoji, count in items_in_inv.items():
        item_data = GAME_ITEMS.get(emoji, {})
        name = item_data.get("name", emoji)
        text += f" {emoji} <b>{name}</b> — {count} шт.\n"

    text += f"\n💰 Сбыть товар можно на рынке: /mgz"
    await message.reply(text, parse_mode="HTML")


# --- КОМАНДА /mgz (Только 5 товаров) ---
@router.message(Command("mgz"))
async def cmd_mgz(message: types.Message):
    update_market()
    rem = int((next_market_update - time.time()) // 60)

    text = (
        "╭ 🛠 <b>РЫНОК ВТОРСЫРЬЯ</b>\n"
        "│\n"
        "╰ <i>Скупщик сегодня ищет только определенные детали...</i>\n\n"
    )

    for item, price in market_prices.items():
        item_data = GAME_ITEMS.get(item, {})
        name = item_data.get("name", "Хлам")
        text += f" {item} {name} ➔ <b>{price}</b> {FARMCOIN}\n"

    text += (
        f"\n━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <b>Цены обновятся через:</b> {rem} мин.\n\n"
        f"💬 <i>Чтобы продать, напиши:</i>\n"
        f"➥ <code>продать [эмодзи] [кол-во]</code>"
    )

    await message.reply(text, parse_mode="HTML")


# --- ТОЧЕЧНАЯ ПРОДАЖА ПРЕДМЕТА ---
@router.message(F.text.lower().startswith("продать "))
async def sell_specific_item(message: types.Message, get_user, save_db):
    update_market()
    parts = message.text.split()

    if len(parts) < 2:
        return await message.reply("⚠️ Укажи что продать. Пример: <code>продать 🔧</code>")

    item_emoji = parts[1]

    # 1. Проверяем, есть ли предмет на рынке сейчас
    if item_emoji not in market_prices:
        return await message.reply("🍂 Ты захотел продать хлам, но он никому не был интересен.")

    user = await get_user(message.from_user.id, message.from_user.username)
    inv = ensure_inv_dict(user)

    # Сколько штук у игрока
    user_has = inv.get(item_emoji, 0)
    if user_has <= 0:
        return await message.reply(f"🙊 У тебя нет предмета {item_emoji} в инвентаре.")

    # 2. Определяем количество для продажи
    amount_to_sell = user_has
    if len(parts) >= 3:
        try:
            val = int(parts[2])
            if val > 0:
                amount_to_sell = min(user_has, val)
        except:
            pass

    # 3. Считаем прибыль
    price = market_prices[item_emoji]
    total_profit = amount_to_sell * price

    # 4. Процесс сделки
    inv[item_emoji] -= amount_to_sell
    if inv[item_emoji] <= 0:
        del inv[item_emoji]

    inv[FARMCOIN] = inv.get(FARMCOIN, 0) + total_profit
    await save_db(message.from_user.id, user)

    item_data = GAME_ITEMS.get(item_emoji, {})
    name = item_data.get("name", "хлам")

    res_text = (
        f"╭ 🤝 <b>УДАЧНАЯ СДЕЛКА</b>\n"
        f"│\n"
        f"╰ Ты сдал {item_emoji} <b>{name}</b> ({amount_to_sell} шт.)\n\n"
        f"💰 <b>Выручка:</b> +{total_profit:,} {FARMCOIN}\n"
        f"👣 <i>Скупщик довольно ухмыльнулся и спрятал товар под прилавок.</i>"
    )

    await message.reply(res_text, parse_mode="HTML")