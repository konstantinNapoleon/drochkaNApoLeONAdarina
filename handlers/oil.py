import time
import random
from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
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


# --- КОМАНДА "МОЯ НЕФТЕБАЗА" ---
# --- КОМАНДА "МОЯ НЕФТЕБАЗА" ---
@router.message(F.text.lower() == "моя нефтебаза")
async def my_oil_base(message: types.Message, get_user):
    user = get_user(message.from_user.id)

    # Получаем данные игрока
    place_id = user.get('oil_place_id', 0)
    place_name = OIL_PLACES.get(place_id, {"name": "Старая скважина"})['name']

    level = user.get('level', 1)
    oil = user.get('oil', 0)

    # Проверка наличия фонарика в инвентаре
    inv = user.get("inventory", {})
    if not isinstance(inv, dict):  # На всякий случай, если инвентарь еще не обновился до словаря
        inv = {}

    has_flashlight = inv.get("🔦", 0) > 0
    flashlight_status = "Есть ✅" if has_flashlight else "Нет ⛔️"

    # Формируем текст по шаблону
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
    # Зашиваем ID пользователя в callback_data, чтобы закрыть мог только он
    builder.add(InlineKeyboardButton(text="❌ Закрыть", callback_data=f"close_base_{message.from_user.id}"))

    await message.reply(text, parse_mode="HTML", reply_markup=builder.as_markup())


# --- ОБРАБОТЧИК КНОПКИ "ЗАКРЫТЬ" (оставь его, если еще не добавил) ---
@router.callback_query(F.data.startswith("close_base_"))
async def close_base_menu(call: types.CallbackQuery):
    owner_id = int(call.data.split("_")[-1])

    if call.from_user.id != owner_id:
        return await call.answer("❌ Это не твоя нефтебаза!", show_alert=True)

    await call.message.delete()


# --- ОБРАБОТЧИК КНОПКИ "ЗАКРЫТЬ" ---
@router.callback_query(F.data.startswith("close_base_"))
async def close_base_menu(call: types.CallbackQuery):
    # Достаем ID владельца меню из callback_data
    owner_id = int(call.data.split("_")[-1])

    # Проверяем, кто нажал на кнопку
    if call.from_user.id != owner_id:
        # Если нажал чужой, выдаем всплывающее уведомление
        return await call.answer("❌ Это не твоя нефтебаза!", show_alert=True)

    # Если нажал владелец — удаляем сообщение
    await call.message.delete()



# --- СИСТЕМА ОПЫТА ---
# --- СИСТЕМА ОПЫТА (XP) ---
def add_xp(user: dict, amount: int):
    user['xp'] = user.get('xp', 0) + amount
    user['level'] = user.get('level', 1)

    leveled_up = 0

    # чтобы можно было апнуться на несколько уровней за раз
    while True:
        xp_needed = user['level'] * 10  # формула как у тебя: lvl*10
        if user['xp'] >= xp_needed:
            user['xp'] -= xp_needed
            user['level'] += 1
            leveled_up += 1
        else:
            break

    next_need = user['level'] * 10
    return leveled_up, next_need


@router.message(F.text.lower() == "добыть нефть")
async def mine_oil(message: types.Message, get_user, save_db):
    user = get_user(message.from_user.id)
    inv = user.get("inventory")
    now = time.time()

    # --- 1. ПРОВЕРКА ШТРАФА ---
    ban_until = user.get('oil_ban_until', 0)
    if ban_until > now:
        rem = int(ban_until - now)
        days = rem // 86400
        hours = (rem % 86400) // 3600

        # Если штраф есть, показываем кнопку "Применить", если лицензия есть в инв.
        builder = InlineKeyboardBuilder()
        if inv.get("📋", 0) > 0:
            builder.row(types.InlineKeyboardButton(text="📋 Применить защиту прав", callback_data="use_oil_license"))

        return await message.answer(
            f"🚫 <b>Госс инспекция наложила штраф!</b>\n"
            f"Тебе запрещено добывать нефть еще: <b>{days}д. {hours}ч.</b>\n\n"
            f"Используй 📋 защиту прав из инвентаря, чтобы снять арест. Жми: /use_oil_license",
            reply_markup=builder.as_markup() if inv.get("📋", 0) > 0 else None,
            parse_mode="HTML"
        )

    # --- 2. СОБЫТИЕ: ШАНС 2% НА ШТРАФ ---
    if random.random() < 0.05:
        user['oil_ban_until'] = now + 172800  # 2 дня
        save_db()

        builder = InlineKeyboardBuilder()
        if inv.get("📋", 0) > 0:
            builder.row(types.InlineKeyboardButton(text="📋 Применить защиту прав", callback_data="use_oil_license"))

        return await message.reply(
            "Ты хотел добыть нефть, но пришла госс инспекция и наложила штраф. "
            "Ты не можешь добывать нефть 2 дня.",
            reply_markup=builder.as_markup() if inv.get("📋", 0) > 0 else None
        )

    # --- 3. ПРОВЕРКА КУЛДАУНА (ТВОЙ КОД) ---
    cooldown = 3600 # 2 часа
    time_passed = now - user.get('last_oil_mine', 0)
    if time_passed < cooldown:
        rem = int(cooldown - time_passed)
        return await message.answer(f"⏳ Скважина пуста. Приходи через {rem // 3600} ч. {(rem % 3600) // 60} мин.")

    # --- 4. ЛОГИКА ДОБЫЧИ (ТВОЙ КОД) ---
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
    leveled_up, next_need = add_xp(user, xp_gain)

    user['oil'] = user.get('oil', 0) + total_liters
    user['last_oil_mine'] = now

    save_db()

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


# Обработчик текстовой команды /use_oil_license
# Обработчик нажатия на КНОПКУ "Применить защиту прав"
@router.callback_query(F.data == "use_oil_license")
async def use_oil_license_callback(callback: types.CallbackQuery, get_user, save_db):
  user = get_user(callback.from_user.id)
  inv = user.get("inventory")
  now = time.time()

  # 1. Проверяем, есть ли штраф
  if user.get('oil_ban_until', 0) <= now:
    await callback.answer("✅ У тебя нет активных штрафов!", show_alert=True)
    return

  # 2. Проверяем наличие лицензии
  if inv.get("📋", 0) <= 0:
    await callback.answer("❌ У тебя нет предмета 📋 Защита прав!", show_alert=True)
    return

  # 3. Применяем
  inv["📋"] -= 1
  user["oil_ban_until"] = 0
  save_db()

  # Отвечаем пользователю и убираем кнопку
  await callback.message.edit_text(
    "✅ Ты предъявил госс инспекции 📋 <b>Защиту прав</b>!\n"
    "Штраф аннулирован. Можешь снова добывать нефть.",
    parse_mode="HTML"
  )
  # Важно: всегда отвечай на callback, чтобы убрать "часики" на кнопке
  await callback.answer("Штраф снят!")


# --- ПОКУПКА МЕСТ (ОБНОВЛЕННАЯ КОМАНДА) ---
# --- ОБЪЕДИНЕННАЯ КОМАНДА ПРОСМОТРА И ПОКУПКИ ---
@router.message(F.text.lower().startswith("приобрести нефтеместо"))
async def handle_oil_places(message: types.Message, get_user, save_db):
    user = get_user(message.from_user.id)
    text_parts = message.text.split()

    # 1. Если просто "Приобрести нефтеместо" (без номера) — показываем список
    if len(text_parts) <= 2:
        text = "<b>🛒 Доступные нефтеместа для покупки:</b>\n\n"
        for i, p in OIL_PLACES.items():
            if i == 0: continue  # Пропускаем стартовую скважину

            status = "✅ Куплено" if user.get('oil_place_id', 0) >= i else f"💰 Цена: {p['price']} л."

            text += (f"{i}. <b>{p['name']}</b>\n"
                     f" 🎖 Требуемый уровень: {p['req_lvl']}\n"
                     f" 📊 Добыча: {p['min']}-{p['max']} л. (+{p['xp']} XP)\n"
                     f" 🏷 {status}\n\n")

        text += "<i>Чтобы купить, напиши: Приобрести нефтеместо [номер]</i>"

        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu"))

        return await message.reply(text, parse_mode="HTML", reply_markup=builder.as_markup())

    # 2. Если есть номер (например, "Приобрести нефтеместо 1") — обрабатываем покупку
    try:
        place_num = int(text_parts[-1])
    except (ValueError, IndexError):
        return await message.reply("❌ Укажи корректный номер места. Пример: <code>Приобрести нефтеместо 1</code>",
                                   parse_mode="HTML")

    if place_num not in OIL_PLACES or place_num == 0:
        return await message.reply("❌ Такого нефтеместа не существует.")

    place = OIL_PLACES[place_num]
    current_lvl = user.get('level', 1)
    current_oil = user.get('oil', 0)

    # Проверка условий
    if current_lvl < place['req_lvl']:
        return await message.reply(f"❌ Недостаточный уровень! Нужен <b>{place['req_lvl']}</b> (у тебя {current_lvl}).",
                                   parse_mode="HTML")

    if current_oil < place['price']:
        return await message.reply(f"❌ Недостаточно нефти! Нужно <b>{place['price']}</b> л. (у тебя {current_oil}).",
                                   parse_mode="HTML")

    if user.get('oil_place_id', 0) >= place_num:
        return await message.reply("❌ Это нефтеместо (или лучше) уже приобретено.")

    # Списание и сохранение
    user['oil'] -= place['price']
    user['oil_place_id'] = place_num
    save_db()

    await message.reply(
        f"💳 <b>Покупка совершена!</b>\n"
        f"Теперь твое основное место добычи: <b>{place['name']}</b>",
        parse_mode="HTML"
    )


# Команда "Купить место" теперь просто вызывает список для удобства
@router.message(F.text.lower() == "купить место")
async def alias_oil_places(message: types.Message, get_user, save_db):
    await handle_oil_places(message, get_user, save_db)

# Колбэк закрытия
@router.callback_query(F.data == "close_menu")
async def close_menu(call: types.CallbackQuery):
    await call.message.delete()


# --- ПРОДАЖА НЕФТИ ---
@router.message(F.text.lower().startswith("продать нефть") | F.text.lower().startswith("/sell_oil"))
async def cmd_sell_oil(message: types.Message, get_user, save_db):
    user = get_user(message.from_user.id)
    inv = user.get("inventory")

    parts = message.text.split()
    try:
        amount = int(parts[-1])
        if amount <= 0: raise ValueError
    except:
        return await message.answer("⚠️ Укажи количество: <code>продать нефть 10</code>", parse_mode="HTML")

    current_oil = user.get("oil", 0)
    if current_oil < amount:
        return await message.answer(f"❌ У тебя нет столько нефти (в наличии: {current_oil} л.)")

    income = amount * OIL_PRICE
    user["oil"] = current_oil - amount
    inv[FARMCOIN_EMOJI] = inv.get(FARMCOIN_EMOJI, 0) + income

    save_db()
    await message.answer(f"✅ Ты продал <b>{amount}</b> л. нефти за <b>{income}</b> {FARMCOIN_EMOJI}", parse_mode="HTML")






