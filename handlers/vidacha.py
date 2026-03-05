from aiogram import Router, F, types

router = Router()

ADMIN_ID = 5006326062
FARMCOIN_EMOJI = "💰"


def ensure_inv_dict(user) -> dict:
    """Гарантирует, что инвентарь — это словарь"""
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        # Если там был список или ничего, превращаем в словарь
        if isinstance(inv, list):
            new_inv = {}
            for item in inv:
                new_inv[item] = new_inv.get(item, 0) + 1
            user["inventory"] = new_inv
        else:
            user["inventory"] = {}
    return user["inventory"]


@router.message(F.text.lower().startswith("выдать "))
async def give_money(message: types.Message, get_user, save_db):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()
    if len(parts) != 3:
        return await message.answer("⚠️ Формат: <code>выдать [ID] [сумма]</code>", parse_mode="HTML")

    try:
        target_id = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        return await message.answer("⚠️ ID и сумма должны быть числами!")

    if amount <= 0:
        return await message.answer("⚠️ Сумма должна быть больше нуля!")

    target_user = get_user(target_id)

    # Получаем инвентарь как словарь
    inv = ensure_inv_dict(target_user)

    # Плюсуем число, а не плодим эмодзи списком
    inv[FARMCOIN_EMOJI] = inv.get(FARMCOIN_EMOJI, 0) + amount

    save_db()

    await message.answer(
        f"✅ Успешно!\n\n"
        f"👤 Пользователю <code>{target_id}</code> выдано <b>{amount:,}</b> {FARMCOIN_EMOJI}.\n"
        f"💰 Теперь всего в инвентаре: <b>{inv[FARMCOIN_EMOJI]:,}</b>",
        parse_mode="HTML"
    )