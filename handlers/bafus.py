from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

ACHIEVEMENTS_LIST = {
    "first_droch": {
        "slot": 1,
        "emoji": "💦",
        "name": "Первая дрочка",
        "desc": "Вы сделали это в первый раз!"
    },
    "whore_winner": {
        "slot": 2,
        "emoji": "💋",
        "name": "Победитель",
        "desc": "Ты получил дрочки от шлюшек (первый выигрыш)."
    },
    "bug_hunter": {
        "slot": 3,
        "emoji": "🐞",
        "name": "Баг-Хантер",
        "desc": "Получил пиздюлей за багоюз."
    },
    "petuh": {
        "slot": 4,
        "emoji": "🐓",
        "name": "Петух",
        "desc": "Ты петух."
    },
    "registration": {
        "slot": 5,
        "emoji": "♦️",
        "name": "Новая кровь",
        "desc": "Официально в деле! Вы нажали /start и начали свой великий путь."
    },
    "banana_legend": {
        "slot": 7,
        "emoji": "🍌",
        "name": "Легенда Банана",
        "desc": "За прохождение сезона ДрочПасса 'Банановый переполох'."
    },

    "olduser": {
        "slot": 6,
        "emoji": "⚜️",
        "name": "Тот самый Олд",
        "desc": "Выдаётся тем людям которые были с ботом когда он исчезал."
    },

    "collector": {
        "slot": 9,
        "emoji": "🎒",
        "name": "Коллекционер",
        "desc": "Собрать 10 предметов в инвентаре"
    }
}


# --- АДМИНСКАЯ КОМАНДА ДЛЯ БАГ-ХАНТЕРА ---
@router.message(Command("ahiv"))
async def admin_give_achievement(message: types.Message, command: CommandObject, get_user, save_db):
    # Добавь сюда проверку на админа, если нужно: if message.from_user.id != ADMIN_ID: return
    target_id = command.args
    if not target_id:
        return await message.reply("Укажи ID пользователя: <code>/ahiv 12345678</code>", parse_mode="HTML")

    user = await get_user(int(target_id), None)
    achievements = user.get("achievements", [])

    if "bug_hunter" not in achievements:
        achievements.append("bug_hunter")
        user["achievements"] = achievements
        await save_db(int(target_id), user)
        await message.reply(f"✅ Ачивка 'Баг-Хантер' выдана пользователю {target_id}")
    else:
        await message.reply("У него уже есть эта ачивка.")


# --- КОМАНДА ДЛЯ АЧИВКИ ПЕТУХ ---
@router.message(F.text.lower() == "я петух")
async def get_petuh_ach(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    achievements = user.get("achievements", [])

    if "petuh" not in achievements:
        achievements.append("petuh")
        user["achievements"] = achievements
        await save_db(message.from_user.id, user)
        await message.reply("🐓 Ты получил ачивку: <b>Петух</b>!", parse_mode="HTML")


# --- ОСТАЛЬНОЙ КОД (БЕЗ ИЗМЕНЕНИЙ) ---

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


@router.message(Command("achievements"))
@router.message(F.text.casefold() == "ачивки")
async def show_achievements(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    user_achievements = user.get("achievements", [])

    if "registration" not in user_achievements:
        user_achievements.append("registration")
        user["achievements"] = user_achievements
        await save_db(message.from_user.id, user)

    grid_text = get_grid_text(user_achievements)
    unlocked_count = sum(1 for ach in user_achievements if ach in ACHIEVEMENTS_LIST)

    text = f"<b>Ачивки</b> 🌼\n\n{grid_text}\n\n🏆 Открыто: {unlocked_count}/{len(ACHIEVEMENTS_LIST)}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️", callback_data=f"achievements_page_list:{message.from_user.id}")]
    ])

    await message.reply(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("achievements_page_list:"))
async def process_achievements_list(callback: types.CallbackQuery, get_user):
    _, owner_id = callback.data.split(":")
    if callback.from_user.id != int(owner_id): return await callback.answer("Это не твои ачивки!", show_alert=True)
    user = await get_user(callback.from_user.id, callback.from_user.username)
    user_achievements = user.get("achievements", [])
    unlocked_achievements = [ach for ach in user_achievements if ach in ACHIEVEMENTS_LIST]

    if not unlocked_achievements:
        text = "У вас пока нет открытых ачивок 😔"
    else:
        text = "📜 <b>Ваши открытые достижения:</b>\n\n"
        for ach_id in unlocked_achievements:
            info = ACHIEVEMENTS_LIST[ach_id]
            text += f"[{info['slot']}] {info['emoji']} <b>{info['name']}</b>\n└ {info['desc']}\n\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️", callback_data=f"achievements_page_grid:{owner_id}")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("achievements_page_grid:"))
async def process_achievements_back(callback: types.CallbackQuery, get_user):
    _, owner_id = callback.data.split(":")
    if callback.from_user.id != int(owner_id): return await callback.answer("Это не твои ачивки!", show_alert=True)
    user = await get_user(callback.from_user.id, callback.from_user.username)
    user_achievements = user.get("achievements", [])
    grid_text = get_grid_text(user_achievements)
    unlocked_count = sum(1 for ach in user_achievements if ach in ACHIEVEMENTS_LIST)
    text = f"<b>Ачивки</b> 🌼\n\n{grid_text}\n\n🏆 Открыто: {unlocked_count}/{len(ACHIEVEMENTS_LIST)}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️", callback_data=f"achievements_page_list:{owner_id}")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

