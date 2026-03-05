import datetime
import html
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject

router = Router()

# Тот самый FARMCOIN_EMOJI (укажи свой, если он другой)
FARMCOIN_EMOJI = "💰"

# Настройка бонус-кодов
BONUS_CODES = {
    "START": {
        "reward": 50,
        "limit": 100,
        "used_count": 0,
        "expires": datetime.datetime(2026, 1, 1),
        "claimed_by": set()  # Используем set для мгновенной проверки
    },
    "GIFT2025": {
        "reward": 100,
        "limit": 10,
        "used_count": 0,
        "expires": datetime.datetime(2025, 6, 1),
        "claimed_by": set()
    }
}


# Функция-помощник для словаря (дублирую, чтобы была под рукой)
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


@router.message(Command("bonuscode"))
async def process_bonus(message: types.Message, command: CommandObject, get_user, save_db):
    if not command.args:
        return await message.reply("⚠️ Введи бонус-код!\nПример: <code>/bonuscode START</code>", parse_mode="HTML")

    code_input = command.args.upper().strip()
    user_id = message.from_user.id

    # 1. Проверка существования кода
    if code_input not in BONUS_CODES:
        return await message.reply("❌ Такого бонус-кода не существует.")

    bonus = BONUS_CODES[code_input]
    now = datetime.datetime.now()

    # 2. Проверки условий
    if now > bonus["expires"]:
        return await message.reply("⌛ Срок действия этого кода истек.")

    if bonus["used_count"] >= bonus["limit"]:
        return await message.reply("🚫 Код больше недоступен (лимит исчерпан).")

    if user_id in bonus["claimed_by"]:
        return await message.reply("🤨 Ты уже активировал этот код!")

    # --- АКТИВАЦИЯ (БЫСТРАЯ) ---
    user = get_user(user_id, message.from_user.username)
    inv = ensure_inv_dict(user)  # Получаем быстрый словарь

    reward_amount = bonus["reward"]

    # Плюсуем число к ключу (вместо расширения списка)
    inv[FARMCOIN_EMOJI] = inv.get(FARMCOIN_EMOJI, 0) + reward_amount

    # Обновляем статистику кода
    bonus["used_count"] += 1
    bonus["claimed_by"].add(user_id)

    save_db()  # Сохраняем изменения в базе

    await message.reply(
        f"✅ <b>Успешно!</b>\n"
        f"Код <code>{code_input}</code> активирован.\n"
        f"Добавлено: <b>{reward_amount}</b> шт. {FARMCOIN_EMOJI}",
        parse_mode="HTML"
    )