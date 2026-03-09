import time
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


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


# --- ОБНОВЛЕННАЯ ФУНКЦИЯ КНОПКИ ---
def get_spray_kb(count: int):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text=f"💦 Применить спрей ({count})",
        callback_data="apply_spray_inline")
    )
    return builder.as_markup()


async def process_droch(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    chat_id = str(message.chat.id)
    inv = ensure_inv_dict(user)
    spray_count = inv.get("💦", 0)  # Получаем количество

    if "chats_data" not in user:
        user["chats_data"] = {}

    if chat_id not in user["chats_data"]:
        user["chats_data"][chat_id] = {
            "masturbations_count": 0,
            "last_droch_time": 0,
            "chat_name": ""
        }

    chat_stats = user["chats_data"][chat_id]
    chat_stats["chat_name"] = message.chat.title or "Личные сообщения"

    COOLDOWN = 1800
    current_time = time.time()
    last_time = chat_stats.get("last_droch_time", 0)
    time_passed = current_time - last_time

    # Кулдаун с количеством в кнопке
    if time_passed < COOLDOWN:
        remaining_seconds = int(COOLDOWN - time_passed)
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        return await message.reply(
            f"Ты недавно дрочил! 🤕 \n"
            f"Приходи через <b>{minutes} мин. {seconds} сек.</b>",
            reply_markup=get_spray_kb(spray_count),
            parse_mode="HTML"
        )

    chat_stats["masturbations_count"] += 1
    chat_stats["last_droch_time"] = current_time

    if "achievements" not in user or not isinstance(user["achievements"], list):
        user["achievements"] = []

    if "first_droch" not in user["achievements"]:
        user["achievements"].append("first_droch")
        await message.answer("🎊 НОВОЕ ДОСТИЖЕНИЕ: ✊ Первая дрочка!\n└ Вы сделали это в первый раз!")

    await save_db(message.from_user.id, user)

    # Успех с количеством в кнопке
    await message.reply(
        f"Ты успешно вздрочнул! 😼\n"
        f"На твоем счету <b>{chat_stats['masturbations_count']}</b> вздрочки.",
        reply_markup=get_spray_kb(spray_count),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "apply_spray_inline")
async def callback_spray(callback: types.CallbackQuery, get_user, save_db):
    user = await get_user(callback.from_user.id, callback.from_user.username)
    chat_id = str(callback.message.chat.id)
    inv = ensure_inv_dict(user)
    spray_count = inv.get("💦", 0)

    if spray_count <= 0:
        return await callback.answer("У тебя нет Спрея для хуя! Купи его в магазине. 🛒", show_alert=True)

    chat_stats = user.get("chats_data", {}).get(chat_id)
    if not chat_stats:
        return await callback.answer("Ошибка данных чата!", show_alert=True)

    COOLDOWN = 1800
    current_time = time.time()
    last_time = chat_stats.get("last_droch_time", 0)

    if (current_time - last_time) < COOLDOWN:
        inv["💦"] = spray_count - 1
        chat_stats["last_droch_time"] = 0
        await save_db(callback.from_user.id, user)

        # Редактируем сообщение (кнопку убираем, так как спрей применен)
        await callback.message.edit_text("Ты применил спрей для хуя. 👍 Жми: /drochnut", reply_markup=None)
    else:
        await callback.answer("Спрей тебе сейчас не нужен! 😝", show_alert=True)

    await callback.answer()


@router.message(Command("drochnut", "дрочнуть"))
async def cmd_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)


@router.message(F.text.lower().in_({"дрочнуть", "юз рука", "юз хуй"}))
async def text_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)