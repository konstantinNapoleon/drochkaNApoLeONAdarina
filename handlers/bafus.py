from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

ACHIEVEMENTS_LIST = {
    "first_droch": {
        "slot": 1,
        "emoji": "💦",
        "name": "Первая дрочка",
        "desc": "Вы сделали это в первый раз!"
    },
    "registration": {
        "slot": 5,
        "emoji": "♦️",
        "name": "Новая кровь",
        "desc": "Официально в деле! Вы нажали /start и начали свой великий путь."
    },
    "collector": {
        "slot": 9,
        "emoji": "🎒",
        "name": "Коллекционер",
        "desc": "Собрать 10 предметов в инвентаре"
    }
}


def get_grid_text(user_achievements):
    grid = ["⚫️"] * 9
    for ach_id in user_achievements:
        if ach_id in ACHIEVEMENTS_LIST:
            slot_index = ACHIEVEMENTS_LIST[ach_id]["slot"] - 1
            if 0 <= slot_index < 9:
                grid[slot_index] = ACHIEVEMENTS_LIST[ach_id]["emoji"]

    return (
        f"{grid[0]} {grid[1]} {grid[2]}\n"
        f"{grid[3]} {grid[4]} {grid[5]}\n"
        f"{grid[6]} {grid[7]} {grid[8]}"
    )


# --- 1. ВЫЗОВ МЕНЮ АЧИВОК (С автовыдачей старым игрокам) ---
@router.message(Command("achievements"))
@router.message(F.text.casefold() == "ачивки")
async def show_achievements(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    user_achievements = user.get("achievements", [])

    # АВТОВЫДАЧА СТАРЫМ ИГРОКАМ
    if "registration" not in user_achievements:
        user_achievements.append("registration")
        user["achievements"] = user_achievements
        await save_db(message.from_user.id, user)  # Сохраняем в БД

    grid_text = get_grid_text(user_achievements)
    unlocked_count = sum(1 for ach in user_achievements if ach in ACHIEVEMENTS_LIST)

    text = f"<b>Ачивки</b> 🌼\n\n{grid_text}\n\n🏆 Открыто: {unlocked_count}/{len(ACHIEVEMENTS_LIST)}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️", callback_data=f"achievements_page_list:{message.from_user.id}")]
    ])

    await message.reply(text, parse_mode="HTML", reply_markup=kb)


# --- 2. ПОКАЗ СПИСКА АЧИВОК (КНОПКА ➡️) ---
@router.callback_query(F.data.startswith("achievements_page_list:"))
async def process_achievements_list(callback: types.CallbackQuery, get_user):
    _, owner_id = callback.data.split(":")

    if callback.from_user.id != int(owner_id):
        return await callback.answer("Это не твои ачивки!", show_alert=True)

    user = await get_user(callback.from_user.id, callback.from_user.username)
    user_achievements = user.get("achievements", [])

    unlocked_achievements = [ach for ach in user_achievements if ach in ACHIEVEMENTS_LIST]

    if not unlocked_achievements:
        text = "У вас пока нет открытых ачивок 😔\nНачните играть, чтобы открыть первую!"
    else:
        text = "📜 <b>Ваши открытые достижения:</b>\n\n"
        for ach_id in unlocked_achievements:
            info = ACHIEVEMENTS_LIST[ach_id]
            text += f"[{info['slot']}] {info['emoji']} <b>{info['name']}</b>\n└ {info['desc']}\n\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️", callback_data=f"achievements_page_grid:{owner_id}")]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


# --- 3. ВОЗВРАТ К СЕТКЕ (КНОПКА ⬅️) ---
@router.callback_query(F.data.startswith("achievements_page_grid:"))
async def process_achievements_back(callback: types.CallbackQuery, get_user):
    _, owner_id = callback.data.split(":")

    if callback.from_user.id != int(owner_id):
        return await callback.answer("Это не твои ачивки!", show_alert=True)

    user = await get_user(callback.from_user.id, callback.from_user.username)
    user_achievements = user.get("achievements", [])

    grid_text = get_grid_text(user_achievements)
    unlocked_count = sum(1 for ach in user_achievements if ach in ACHIEVEMENTS_LIST)

    text = f"<b>Ачивки</b> 🌼\n\n{grid_text}\n\n🏆 Открыто: {unlocked_count}/{len(ACHIEVEMENTS_LIST)}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️", callback_data=f"achievements_page_list:{owner_id}")]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

    #nen делаем репозиторийпш