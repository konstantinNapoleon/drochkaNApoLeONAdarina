import html
from datetime import datetime, timezone, timedelta
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# Часовой пояс МСК (UTC+3), чтобы день сбрасывался правильно по московскому времени
MSK_TZ = timezone(timedelta(hours=3))


def get_current_date_str():
    """Возвращает текущую дату в формате YYYY-MM-DD по МСК"""
    return datetime.now(MSK_TZ).strftime("%Y-%m-%d")


# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ КНОПОК ---
def get_top_kb(current_view="users"):
    """
    Создает клавиатуру.
    current_view: "users" (Топ игроков), "chats" (Топ чатов), "today" (Топ сегодня)
    """
    builder = InlineKeyboardBuilder()

    if current_view == "users":
        builder.row(types.InlineKeyboardButton(text="🏢 Топ чаты", callback_data="top_chats"))
        builder.row(types.InlineKeyboardButton(text="🔥 За сегодня", callback_data="top_today"))
    elif current_view == "chats":
        builder.row(types.InlineKeyboardButton(text="👤 Топ игроков", callback_data="back_to_top_users"))
        builder.row(types.InlineKeyboardButton(text="🔥 За сегодня", callback_data="top_today"))
    elif current_view == "today":
        builder.row(types.InlineKeyboardButton(text="👤 За все время", callback_data="back_to_top_users"))
        builder.row(types.InlineKeyboardButton(text="🏢 Топ чаты", callback_data="top_chats"))

    builder.row(types.InlineKeyboardButton(text="❌ Закрыть", callback_data="close_top"))
    return builder.as_markup()


# --- ОСНОВНОЙ ТОП ИГРОКОВ (ЗА ВСЕ ВРЕМЯ) ---
@router.message(Command("topdroch", "топдроч"))
async def cmd_top_droch(message: types.Message, get_all_users):
    all_users = await get_all_users()
    drocher_scores = []

    for user_id, user_data in all_users.items():
        chats_data = user_data.get("chats_data", {})

        # Суммируем только если ID чата < 0 (это группы)
        total = sum(
            chat_stats.get("masturbations_count", 0)
            for cid, chat_stats in chats_data.items()
            if int(cid) < 0
        )

        if total > 0:
            name = user_data.get("first_name") or user_data.get("username") or f"Игрок {str(user_id)[-4:]}"
            drocher_scores.append({"name": name, "score": total})

    drocher_scores.sort(key=lambda x: x["score"], reverse=True)

    if not drocher_scores:
        return await message.answer("В группах пока никто не дрочил! 🙄")

    text = "🏆 <b>ТОП-10 ДРОЧЕРОВ (ЗА ВСЕ ВРЕМЯ):</b>\n\n"
    for i, user in enumerate(drocher_scores[:10], 1):
        text += f"<b>{i}.</b> {html.escape(str(user['name']))} — {user['score']} раз\n"

    await message.answer(text, parse_mode="HTML", reply_markup=get_top_kb("users"))


# --- ТОП ЧАТОВ (ТОЛЬКО ГРУППЫ) ---
@router.callback_query(F.data == "top_chats")
async def process_top_chats(callback: types.CallbackQuery, get_all_users):
    all_users = await get_all_users()
    chat_totals = {}

    for user_data in all_users.values():
        chats_data = user_data.get("chats_data", {})
        for chat_id, chat_stats in chats_data.items():

            # Игнорируем ЛС (ID >= 0)
            if int(chat_id) >= 0:
                continue

            count = chat_stats.get("masturbations_count", 0)
            if count <= 0: continue

            if chat_id not in chat_totals:
                chat_totals[chat_id] = {"name": None, "score": 0}

            chat_totals[chat_id]["score"] += count
            name = chat_stats.get("chat_name")
            if name and not chat_totals[chat_id]["name"]:
                chat_totals[chat_id]["name"] = name

    sorted_chats = sorted(chat_totals.values(), key=lambda x: x["score"], reverse=True)

    if not sorted_chats:
        return await callback.answer("Статистики групп еще нет!", show_alert=True)

    text = "🏢 <b>ТОП ЧАТОВ ПО ДРОЧКЕ:</b>\n\n"
    for i, chat in enumerate(sorted_chats[:10], 1):
        display_name = chat["name"] if chat["name"] else "Скрытая группа"
        text += f"<b>{i}.</b> {html.escape(str(display_name))} — {chat['score']} раз\n"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_top_kb("chats"))


# --- ТОП ЗА СЕГОДНЯ ---
@router.callback_query(F.data == "top_today")
async def process_top_today(callback: types.CallbackQuery, get_all_users):
    all_users = await get_all_users()
    today_scores = []
    current_date = get_current_date_str()

    for user_id, user_data in all_users.items():
        daily_stats = user_data.get("daily_stats", {})

        # Проверяем, дрочил ли человек сегодня
        today_count = daily_stats.get(current_date, 0)

        if today_count > 0:
            name = user_data.get("first_name") or user_data.get("username") or f"Игрок {str(user_id)[-4:]}"
            today_scores.append({"name": name, "score": today_count})

    today_scores.sort(key=lambda x: x["score"], reverse=True)

    if not today_scores:
        # Если за сегодня еще никто не дрочил
        text = "🔥 <b>ТОП ДРОЧЕРОВ ЗА СЕГОДНЯ:</b>\n\n<i>Сегодня пока никто не проявлял активность! Будь первым! 💦</i>"
        return await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_top_kb("today"))

    text = "🔥 <b>ТОП-10 ДРОЧЕРОВ ЗА СЕГОДНЯ:</b>\n\n"
    for i, user in enumerate(today_scores[:10], 1):
        text += f"<b>{i}.</b> {html.escape(str(user['name']))} — {user['score']} раз\n"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_top_kb("today"))


# --- ВОЗВРАТ К ТОПУ ИГРОКОВ (ЗА ВСЕ ВРЕМЯ) ---
@router.callback_query(F.data == "back_to_top_users")
async def back_to_users(callback: types.CallbackQuery, get_all_users):
    all_users = await get_all_users()
    drocher_scores = []

    for user_id, user_data in all_users.items():
        chats_data = user_data.get("chats_data", {})

        total = sum(
            chat_stats.get("masturbations_count", 0)
            for cid, chat_stats in chats_data.items()
            if int(cid) < 0
        )

        if total > 0:
            name = user_data.get("first_name") or user_data.get("username") or f"Игрок {str(user_id)[-4:]}"
            drocher_scores.append({"name": name, "score": total})

    drocher_scores.sort(key=lambda x: x["score"], reverse=True)

    text = "🏆 <b>ТОП-10 ДРОЧЕРОВ (ЗА ВСЕ ВРЕМЯ):</b>\n\n"
    for i, user in enumerate(drocher_scores[:10], 1):
        text += f"<b>{i}.</b> {html.escape(str(user['name']))} — {user['score']} раз\n"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_top_kb("users"))


# --- ЗАКРЫТЬ МЕНЮ ---
@router.callback_query(F.data == "close_top")
async def close_top_menu(callback: types.CallbackQuery):
    await callback.message.delete()