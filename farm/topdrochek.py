import html
from datetime import datetime, timezone, timedelta
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()
MSK_TZ = timezone(timedelta(hours=3))


def get_current_date_str():
    return datetime.now(MSK_TZ).strftime("%Y-%m-%d")


def get_top_kb(current_view="users"):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="👤 Игроки", callback_data="back_to_top_users"),
        types.InlineKeyboardButton(text="🏢 Чаты", callback_data="top_chats")
    )
    builder.row(
        types.InlineKeyboardButton(text="🔥 Сегодня", callback_data="top_today"),
        types.InlineKeyboardButton(text="📅 Неделя", callback_data="top_week")
    )
    builder.row(types.InlineKeyboardButton(text="❌ Закрыть", callback_data="close_top"))
    return builder.as_markup()


# --- ВСЕ ВРЕМЯ (ТОП 15 ИГРОКОВ) ---
@router.message(Command("topdroch", "топдроч"))
async def cmd_top_droch(message: types.Message, get_all_users):
    all_users = await get_all_users()

    scores = []
    for u in all_users.values():
        # Считаем сумму по ВСЕМ чатам (и ЛС, и Группы), чтобы игрок видел свой полный прогресс
        total_score = sum(c.get("masturbations_count", 0) for c in u.get("chats_data", {}).values())
        if total_score > 0:
            scores.append({
                "name": u.get("first_name") or u.get("username") or "Аноним",
                "score": total_score
            })

    scores = sorted(scores, key=lambda x: x["score"], reverse=True)

    text = "🏆 <b>ТОП-15 ДРОЧЕРОВ (ВСЁ ВРЕМЯ):</b>\n\n" + "".join(
        [f"<b>{i}.</b> {html.escape(str(u['name']))} — {u['score']} раз\n"
         for i, u in enumerate(scores[:15], 1)]
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_top_kb("users"))


# --- НЕДЕЛЯ (ТОП 15) ---
@router.callback_query(F.data == "top_week")
async def process_top_week(callback: types.CallbackQuery, get_all_users):
    all_users = await get_all_users()
    week_scores = {}
    today = datetime.now(MSK_TZ)
    start_of_week = today - timedelta(days=today.weekday())

    for user_data in all_users.values():
        total_week = sum(count for d_str, count in user_data.get("daily_stats", {}).items()
                         if datetime.strptime(d_str, "%Y-%m-%d").replace(tzinfo=MSK_TZ) >= start_of_week)
        if total_week > 0:
            name = user_data.get("first_name") or user_data.get("username") or "Аноним"
            week_scores[name] = week_scores.get(name, 0) + total_week

    sorted_scores = sorted(week_scores.items(), key=lambda x: x[1], reverse=True)
    text = "📅 <b>ТОП-15 ДРОЧЕРОВ ЗА НЕДЕЛЮ:</b>\n\n" + "".join(
        [f"<b>{i}.</b> {html.escape(str(n))} — {s} раз\n" for i, (n, s) in enumerate(sorted_scores[:15], 1)])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_top_kb("week"))


# --- ЧАТЫ (ТОП 15 ГРУПП) ---
@router.callback_query(F.data == "top_chats")
async def process_top_chats(callback: types.CallbackQuery, get_all_users):
    all_users = await get_all_users()
    chat_totals = {}

    for user_data in all_users.values():
        for chat_id, chat_stats in user_data.get("chats_data", {}).items():
            # ОСТАВЛЯЕМ ПРОВЕРКУ: считаем только группы (ID < 0), чтобы ЛС не попадали в список чатов
            if int(chat_id) < 0:
                count = chat_stats.get("masturbations_count", 0)
                if count > 0:
                    if chat_id not in chat_totals:
                        chat_totals[chat_id] = {"name": chat_stats.get("chat_name") or "Группа", "score": 0}
                    chat_totals[chat_id]["score"] += count

    sorted_chats = sorted(chat_totals.values(), key=lambda x: x["score"], reverse=True)
    text = "🏢 <b>ТОП-15 ЧАТОВ:</b>\n\n" + "".join(
        [f"<b>{i}.</b> {html.escape(str(c['name']))} — {c['score']} раз\n" for i, c in
         enumerate(sorted_chats[:15], 1)])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_top_kb("chats"))


# --- СЕГОДНЯ (ТОП 15) ---
@router.callback_query(F.data == "top_today")
async def process_top_today(callback: types.CallbackQuery, get_all_users):
    all_users = await get_all_users()
    today = get_current_date_str()

    scores = []
    for u in all_users.values():
        daily_count = u.get("daily_stats", {}).get(today, 0)
        if daily_count > 0:
            scores.append({
                "name": u.get("first_name") or u.get("username") or "Аноним",
                "score": daily_count
            })

    scores = sorted(scores, key=lambda x: x["score"], reverse=True)

    text = "🔥 <b>ТОП-15 ЗА СЕГОДНЯ:</b>\n\n" + "".join(
        [f"<b>{i}.</b> {html.escape(str(u['name']))} — {u['score']} раз\n" for i, u in enumerate(scores[:15], 1)])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_top_kb("today"))


@router.callback_query(F.data == "back_to_top_users")
async def back_to_users(callback: types.CallbackQuery, get_all_users):
    all_users = await get_all_users()

    scores = []
    for u in all_users.values():
        # Повторяем логику полного зачета для кнопки "Назад"
        total_score = sum(c.get("masturbations_count", 0) for c in u.get("chats_data", {}).values())
        if total_score > 0:
            scores.append({
                "name": u.get("first_name") or u.get("username") or "Аноним",
                "score": total_score
            })

    scores = sorted(scores, key=lambda x: x["score"], reverse=True)

    text = "🏆 <b>ТОП-15 ДРОЧЕРОВ (ВСЁ ВРЕМЯ):</b>\n\n" + "".join(
        [f"<b>{i}.</b> {html.escape(str(u['name']))} — {u['score']} раз\n" for i, u in enumerate(scores[:15], 1)])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_top_kb("users"))


@router.callback_query(F.data == "close_top")
async def close_top_menu(callback: types.CallbackQuery):
    await callback.message.delete()