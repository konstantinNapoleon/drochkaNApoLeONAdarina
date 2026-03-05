import html
from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("topdroch", "топдроч"))
async def cmd_top_droch(message: types.Message, get_all_users):
    all_users = get_all_users()

    drocher_scores = []

    # Перебираем всех пользователей
    for user_id, user_data in all_users.items():
        chats_data = user_data.get("chats_data", {})
        total = sum(chat_stats.get("masturbations_count", 0) for chat_stats in chats_data.values())

        if total > 0:
            # Сначала пытаемся взять Имя (first_name), если нет — Юзернейм, если и его нет — заглушка
            name = user_data.get("first_name") or user_data.get("username") or f"Игрок {str(user_id)[-4:]}"

            drocher_scores.append({
                "name": name,
                "score": total
            })

    # Сортировка по убыванию количества
    drocher_scores.sort(key=lambda x: x["score"], reverse=True)

    if not drocher_scores:
        return await message.answer("Топ пока пуст! 🙄")

    # Формируем текст списка
    text = "🏆 <b>ТОП-10 ДРОЧЕРОВ:</b>\n\n"
    for i, user in enumerate(drocher_scores[:10], 1):
        # Вывод в формате: 1. Иван — 10 раз
        text += f"{i}. <b>{html.escape(str(user['name']))}</b> — {user['score']} раз\n"

    await message.answer(text, parse_mode="HTML")