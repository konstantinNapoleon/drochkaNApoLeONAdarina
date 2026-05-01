import html
import random
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

ACTIVE_GAMES = {}
EMOJI_PAIRS = [("🍌", "🍑"), ("🍆", "🍒")]
FARMCOIN_EMOJI = "💰"


# Защита от отсутствия инвентаря у пользователя
def ensure_inv_dict(user) -> dict:
    if user is None:
        return {}
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        user["inventory"] = {}
    return user["inventory"]


def check_winner(board):
    win_coords = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
    for c in win_coords:
        if board[c[0]] == board[c[1]] == board[c[2]] != "empty":
            return board[c[0]]
    if "empty" not in board:
        return "draw"
    return None


def get_board_markup(game_id, board, status="playing"):
    builder = InlineKeyboardBuilder()
    for i in range(9):
        val = board[i]
        text = " " if val == "empty" else val
        if status == "playing" and val == "empty":
            # Укороченный callback (ttt_m вместо ttt_move) для защиты от лимитов длины кнопок в Telegram
            builder.button(text=text, callback_data=f"ttt_m:{game_id}:{i}")
        else:
            builder.button(text=text, callback_data="ttt_none")

    builder.adjust(3)
    if status == "playing":
        builder.row(types.InlineKeyboardButton(text="Отменить игру", callback_data=f"ttt_c:{game_id}"))
    return builder.as_markup()


@router.message(F.text.lower().startswith("кн"))
async def start_ttt(message: types.Message, get_user, save_db):
    if not message.reply_to_message:
        return await message.reply("Эту команду нужно писать в ответ пользователю!")

    parts = message.text.split()
    try:
        bet = int(parts[1])
        if not (50 <= bet <= 500):
            return await message.reply("Ставка должна быть от 50 до 500 💰!")
    except (IndexError, ValueError):
        return await message.reply("Напиши: кн [ставка] (например, кн 100)")

    host_id = int(message.from_user.id)
    opp_id = int(message.reply_to_message.from_user.id)

    if host_id == opp_id:
        return await message.reply("Нельзя играть с самим собой!")

    # Ищем хоста
    h_username = message.from_user.username or "player"
    h_user = await get_user(host_id, h_username)

    if ensure_inv_dict(h_user).get(FARMCOIN_EMOJI, 0) < bet:
        return await message.reply(
            f"У тебя не хватает 💰! Твой баланс: {ensure_inv_dict(h_user).get(FARMCOIN_EMOJI, 0)}")

    # Уникальный ID из номера сообщения
    game_id = f"{message.message_id % 100000}"
    p1_e, p2_e = random.choice(EMOJI_PAIRS)

    # Сохраняем и first_name (для отображения) и username (для базы данных)
    n1 = message.from_user.first_name or "Игрок 1"
    n2 = message.reply_to_message.from_user.first_name or "Игрок 2"
    u1 = message.from_user.username or "player"
    u2 = message.reply_to_message.from_user.username or "player"

    ACTIVE_GAMES[game_id] = {
        "host": host_id,
        "opponent": opp_id,
        "bet": bet,
        "board": ["empty"] * 9,
        "turn": opp_id,  # Оппонент ходит первым
        "emojis": {host_id: p1_e, opp_id: p2_e},
        "names": {host_id: n1, opp_id: n2},
        "usernames": {host_id: u1, opp_id: u2},  # Вот это починит баг с выдачей приза!
        "checked_opp": False
    }

    text = (
        f"<b>Крестики-нолики на {bet} 💰!</b>\n\n"
        f"{p1_e} {html.escape(n1)}\n"
        f"{p2_e} {html.escape(n2)} 👈"
    )
    await message.answer(text, reply_markup=get_board_markup(game_id, ACTIVE_GAMES[game_id]["board"]),
                         parse_mode="HTML")


@router.callback_query(F.data.startswith("ttt_m:"))
async def process_ttt_move(callback: types.CallbackQuery, get_user, save_db):
    _, game_id, index = callback.data.split(":")
    index = int(index)
    game = ACTIVE_GAMES.get(game_id)

    if not game:
        try:
            await callback.answer("Игра не найдена или уже завершена.", show_alert=True)
        except:
            pass
        return

    player_id = int(callback.from_user.id)

    # ПРОВЕРКА ОЧЕРЕДИ
    if player_id != game["turn"]:
        return await callback.answer("Сейчас не твой ход!", show_alert=True)

    # ПРОВЕРКА БАЛАНСА ВТОРОГО ИГРОКА
    if not game["checked_opp"]:
        opp_username = callback.from_user.username or "player"
        u = await get_user(player_id, opp_username)
        if u is None or ensure_inv_dict(u).get(FARMCOIN_EMOJI, 0) < game["bet"]:
            return await callback.answer("У тебя не хватает 💰 для игры!", show_alert=True)
        game["checked_opp"] = True

    # СТАВИМ ЭМОДЗИ И МЕНЯЕМ ХОД
    emoji = game["emojis"][player_id]
    game["board"][index] = emoji
    game["turn"] = game["opponent"] if player_id == game["host"] else game["host"]

    # ПРОВЕРЯЕМ ПОБЕДИТЕЛЯ
    winner = check_winner(game["board"])

    if winner:
        # --- ФИНАЛ ИГРЫ ---
        if winner == "draw":
            res_text = "<b>Ничья!</b> 💰 остались при своих."
        else:
            win_id = game["host"] if winner == game["emojis"][game["host"]] else game["opponent"]
            los_id = game["opponent"] if win_id == game["host"] else game["host"]

            res_text = f"<b>{html.escape(game['names'][win_id])} победил!</b>\nПолучено: {game['bet']} 💰"

            # ВЫДАЧА НАГРАДЫ (Обернута в try-except для надежности)
            try:
                w_u = await get_user(win_id, game["usernames"][win_id])
                l_u = await get_user(los_id, game["usernames"][los_id])

                if w_u and l_u:
                    ensure_inv_dict(w_u)[FARMCOIN_EMOJI] = ensure_inv_dict(w_u).get(FARMCOIN_EMOJI, 0) + game["bet"]
                    ensure_inv_dict(l_u)[FARMCOIN_EMOJI] = ensure_inv_dict(l_u).get(FARMCOIN_EMOJI, 0) - game["bet"]

                    await save_db(win_id, w_u)
                    await save_db(los_id, l_u)
            except Exception as e:
                print(f"Ошибка при выдаче Фармкоинов в крестиках-ноликах: {e}")
                res_text += "\n<i>(Ошибка при начислении монет)</i>"

        # ОБНОВЛЯЕМ ПОЛЕ (Даже если выдача награды сломалась)
        await callback.message.edit_text(
            f"Игра окончена!\n{res_text}",
            reply_markup=get_board_markup(game_id, game["board"], status="finished"),
            parse_mode="HTML"
        )
        del ACTIVE_GAMES[game_id]
    else:
        # --- ИГРА ПРОДОЛЖАЕТСЯ ---
        text = (
            f"<b>Крестики-нолики на {game['bet']} 💰!</b>\n\n"
            f"{game['emojis'][game['host']]} {html.escape(game['names'][game['host']])} {'👈' if game['turn'] == game['host'] else ''}\n"
            f"{game['emojis'][game['opponent']]} {html.escape(game['names'][game['opponent']])} {'👈' if game['turn'] == game['opponent'] else ''}"
        )
        await callback.message.edit_text(text, reply_markup=get_board_markup(game_id, game["board"]), parse_mode="HTML")

    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data.startswith("ttt_c:"))
async def cancel_ttt(callback: types.CallbackQuery):
    _, game_id = callback.data.split(":")
    game = ACTIVE_GAMES.get(game_id)
    if game and int(callback.from_user.id) in [game["host"], game["opponent"]]:
        del ACTIVE_GAMES[game_id]
        await callback.message.edit_text("Игра отменена.")
    else:
        try:
            await callback.answer("Только игроки могут отменить игру!", show_alert=True)
        except:
            pass


@router.callback_query(F.data == "ttt_none")
async def ttt_none(callback: types.CallbackQuery):
    try:
        await callback.answer()
    except:
        pass

