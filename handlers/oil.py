import time
import random
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

OIL_PRICE = 50
FARMCOIN_EMOJI = "💰"
LICENSE_EMOJI = "📋"
FLASH_LIGHT = "🔦"

# Данные о локациях
OIL_PLACES = {
    0: {"name": "🕳 | ЗАБРОШЕННАЯ НЕФТЯНАЯ СКВАЖИНА", "min": 1, "max": 10, "xp": 5, "price": 0, "req_lvl": 1},
    1: {"name": "⛰ | Горный карьер с буровой установкой", "min": 15, "max": 30, "xp": 15, "price": 300, "req_lvl": 15},
    2: {"name": "🏭 | Нефтяная база с насосами", "min": 35, "max": 60, "xp": 25, "price": 1500, "req_lvl": 35},
    3: {"name": "🏗 | Нефтяная вышка на Тихом океане", "min": 70, "max": 100, "xp": 50, "price": 5000, "req_lvl": 80}
}


# --- СИСТЕМА ОПЫТА ---
def add_xp(user: dict, amount: int):
    user['xp'] = user.get('xp', 0) + amount
    user['level'] = user.get('level', 1)
    leveled_up = 0
    while True:
        xp_needed = user['level'] * 10
        if user['xp'] >= xp_needed:
            user['xp'] -= xp_needed
            user['level'] += 1
            leveled_up += 1
        else:
            break
    next_need = user['level'] * 10
    return leveled_up, next_need


# --- КОМАНДА "МОЯ НЕФТЕБАЗА" ---
@router.message(F.text.lower() == "моя нефтебаза")
async def my_oil_base(message: types.Message, get_user):
    user = await get_user(message.from_user.id, message.from_user.username)

    place_id = user.get('oil_place_id', 0)
    place_name = OIL_PLACES.get(place_id, {"name": "Старая скважина"})['name']
    level = user.get('level', 1)
    oil = user.get('oil', 0)

    inv = user.get("inventory", {})
    if not isinstance(inv, dict):
        inv = {}

    has_flashlight = inv.get(FLASH_LIGHT, 0) > 0
    flashlight_status = "Есть ✅" if has_flashlight else "Нет ⛔️"

    text = (
        "🏰| Твоя фактическая Нефте-база!\n\n"
        f"📍 Место добычи: <b>{place_name}</b>\n"
        "—————————————\n"
        f"🎖 Уровень: <b>{level}</b>\n"
        "—————————————\n"
        f"🛢 Запасы: <b>{oil} л.</b>\n"
        "—————————————\n"
        f"🔦 - фонарик ({flashlight_status})"
    )

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Закрыть", callback_data=f"close_base_{message.from_user.id}"))
    await message.reply(text, parse_mode="HTML", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("close_base_"))
async def close_base_menu(call: types.CallbackQuery):
    owner_id = int(call.data.split("_")[-1])
    if call.from_user.id != owner_id:
        return await call.answer("❌ Это не твоя нефтебаза!", show_alert=True)
    await call.message.delete()


# --- ДОБЫЧА НЕФТИ ---
@router.message(F.text.lower() == "добыть нефть")
async def mine_oil(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    inv = user.get("inventory", {})
    now = time.time()

    ban_until = user.get('oil_ban_until', 0)
    if ban_until > now:
        rem = int(ban_until - now)
        days = rem // 86400
        hours = (rem % 86400) // 3600
        builder = InlineKeyboardBuilder()
        if inv.get(LICENSE_EMOJI, 0) > 0:
            builder.row(types.InlineKeyboardButton(text="📋 Применить защиту прав", callback_data="use_oil_license"))
        return await message.answer(
            f"🚫 <b>Госс инспекция наложила штраф!</b>\n"
            f"Тебе запрещено добывать нефть еще: <b>{days}д. {hours}ч.</b>\n\n"
            f"Используй 📋 защиту прав из инвентаря, чтобы снять арест. Жми: /use_oil_license",
            reply_markup=builder.as_markup() if inv.get(LICENSE_EMOJI, 0) > 0 else None,
            parse_mode="HTML"
        )

    if random.random() < 0.05:
        user['oil_ban_until'] = now + 172800
        await save_db(message.from_user.id, user)
        builder = InlineKeyboardBuilder()
        if inv.get(LICENSE_EMOJI, 0) > 0:
            builder.row(types.InlineKeyboardButton(text="📋 Применить защиту прав", callback_data="use_oil_license"))
        return await message.reply(
            "Ты хотел добыть нефть, но пришла госс инспекция и наложила штраф. Ты не можешь добывать нефть 2 дня.",
            reply_markup=builder.as_markup() if inv.get(LICENSE_EMOJI, 0) > 0 else None
        )

    cooldown = 7200
    time_passed = now - user.get('last_oil_mine', 0)
    if time_passed < cooldown:
        rem = int(cooldown - time_passed)
        return await message.answer(f"⏳ Скважина пуста. Приходи через {rem // 3600} ч. {(rem % 3600) // 60} мин.")

    place_id = user.get('oil_place_id', 0)
    place = OIL_PLACES.get(place_id, OIL_PLACES[0])
    base_liters = random.randint(place["min"], place["max"])
    total_liters = base_liters
    bonus_text = ""

    if inv.get(FLASH_LIGHT, 0) > 0:
        bonus = random.randint(1, 5)
        total_liters += bonus
        bonus_text = f"\n{FLASH_LIGHT} Ты посветил фонариком и добыл еще <b>{bonus}</b> л."

    xp_gain = place.get('xp', 5)
    leveled_up, _ = add_xp(user, xp_gain)
    user['oil'] = user.get('oil', 0) + total_liters
    user['last_oil_mine'] = now

    await save_db(message.from_user.id, user)

    lvl_up_msg = f"\n\n⬆️ <b>LEVEL UP!</b> Ты достиг <b>{user['level']}</b> уровня! 🎉" if leveled_up > 0 else ""
    text = (
        f"📍 <b>{place['name']}</b>\n\n"
        f"⬛ Ты добыл: <b>+{base_liters}</b> л. нефти\n"
        f"✨ Опыт: <b>+{xp_gain}</b> XP 📈{bonus_text}\n\n"
        f"Твои запасы 🛢: <b>{user['oil']}</b> л.\n"
        f"🆙 Твой уровень: <b>{user['level']}</b> [{user['xp']}/{user['level'] * 10} XP]"
        f"{lvl_up_msg}\n"
        "<i>Следующая попытка через 2 часа.</i>"
    )
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "use_oil_license")
async def use_oil_license_callback(callback: types.CallbackQuery, get_user, save_db):
    user = await get_user(callback.from_user.id, callback.from_user.username)
    inv = user.get("inventory", {})
    now = time.time()

    if user.get('oil_ban_until', 0) <= now:
        return await callback.answer("✅ У тебя нет активных штрафов!", show_alert=True)
    if inv.get(LICENSE_EMOJI, 0) <= 0:
        return await callback.answer("❌ У тебя нет предмета 📋 Защита прав!", show_alert=True)

    inv[LICENSE_EMOJI] -= 1
    user["oil_ban_until"] = 0
    await save_db(callback.from_user.id, user)

    await callback.message.edit_text("✅ Ты предъявил госс инспекции 📋 <b>Защиту прав</b>!\nШтраф аннулирован.",
                                     parse_mode="HTML")
    await callback.answer("Штраф снят!")


@router.message(F.text.lower().startswith("приобрести нефтеместо"))
async def handle_oil_places(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    text_parts = message.text.split()

    if len(text_parts) <= 2:
        text = "<b>🛒 Доступные нефтеместа для покупки:</b>\n\n"
        for i, p in OIL_PLACES.items():
            if i == 0: continue
            status = "✅ Куплено" if user.get('oil_place_id', 0) >= i else f"💰 Цена: {p['price']} л."
            text += f"{i}. <b>{p['name']}</b>\n 🎖 Уровень: {p['req_lvl']}\n 🏷 {status}\n\n"
        text += "<i>Напиши: Приобрести нефтеместо [номер]</i>"
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu"))
        return await message.reply(text, parse_mode="HTML", reply_markup=builder.as_markup())

    try:
        place_num = int(text_parts[-1])
        place = OIL_PLACES[place_num]
    except:
        return await message.reply("❌ Укажи корректный номер места.")

    if user.get('level', 1) < place['req_lvl'] or user.get('oil', 0) < place['price']:
        return await message.reply("❌ Недостаточно уровня или нефти!")

    if user.get('oil_place_id', 0) >= place_num:
        return await message.reply("❌ Это нефтеместо уже приобретено.")

    user['oil'] -= place['price']
    user['oil_place_id'] = place_num
    await save_db(message.from_user.id, user)
    await message.reply(f"💳 <b>Покупка совершена!</b>\nТеперь твое место: <b>{place['name']}</b>", parse_mode="HTML")


@router.message(F.text.lower().startswith("продать нефть"))
async def cmd_sell_oil(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    inv = user.get("inventory", {})
    parts = message.text.split()
    try:
        amount = int(parts[-1])
        if amount <= 0: raise ValueError
    except:
        return await message.answer("⚠️ Укажи количество: <code>продать нефть 10</code>", parse_mode="HTML")

    if user.get("oil", 0) < amount:
        return await message.answer(f"❌ Недостаточно нефти (есть {user.get('oil', 0)} л.)")

    income = amount * OIL_PRICE
    user["oil"] -= amount
    inv[FARMCOIN_EMOJI] = inv.get(FARMCOIN_EMOJI, 0) + income

    await save_db(message.from_user.id, user)
    await message.answer(f"✅ Ты продал <b>{amount}</b> л. нефти за <b>{income}</b> {FARMCOIN_EMOJI}", parse_mode="HTML")


@router.callback_query(F.data == "close_menu")
async def close_menu(call: types.CallbackQuery):
    await call.message.delete()








