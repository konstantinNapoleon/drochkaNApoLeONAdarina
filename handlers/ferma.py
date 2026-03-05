import html
import re
from aiogram import Router, types, F
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем твои данные
from items import GAME_ITEMS

router = Router()


# Твоя функция для инвентаря (вставь её или импортируй)
def get_inv_dict(user) -> dict:
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


# Фабрика кнопок
class TradeCallback(CallbackData, prefix="trade"):
    action: str
    init_id: int
    target_id: int
    it1: str
    c1: int
    it2: str
    c2: int


@router.message(F.text.lower().startswith("обмен"))
async def cmd_trade_start(message: types.Message, get_user, save_db):
 if not message.reply_to_message:
  return await message.reply("Нужно ответить реплаем на сообщение того, с кем хочешь обменяться!")

 id_a = message.from_user.id
 id_b = message.reply_to_message.from_user.id

 if id_a == id_b:
  return await message.reply("❌ Нельзя меняться с самим собой!")

 pattern = r"обмен\s+(\S+)\s+(\d+)\s+(\S+)\s+(\d+)"
 match = re.search(pattern, message.text, re.IGNORECASE)
 if not match:
  return await message.reply("❌ Формат: <code>обмен 💰 100 🔦 1</code>", parse_mode="HTML")

 it1, c1, it2, c2 = match.groups()
 c1, c2 = int(c1), int(c2)

 user_a = get_user(id_a, message.from_user.username)
 user_b = get_user(id_b, message.reply_to_message.from_user.username)

 user_a['first_name'] = message.from_user.first_name
 user_b['first_name'] = message.reply_to_message.from_user.first_name
 save_db()

 inv_a = get_inv_dict(user_a)
 inv_b = get_inv_dict(user_b)

 if inv_a.get(it1, 0) < c1 or inv_b.get(it2, 0) < c2:
  return await message.reply("😭 Недостаточно предметов.")

 # Тут просто текст, БЕЗ ссылок
 name_a = html.escape(user_a["first_name"])
 name_b = html.escape(user_b["first_name"])

 builder = InlineKeyboardBuilder()
 data = {"init_id": id_a, "target_id": id_b, "it1": it1, "c1": c1, "it2": it2, "c2": c2}
 builder.button(text="👌 Подтвердить", callback_data=TradeCallback(action="confirm1", **data))
 builder.button(text="Отмена 💔", callback_data=TradeCallback(action="cancel1", **data))
 builder.adjust(2)

 await message.reply(
  f"Вы хотите передать {c1} {it1} в обмен на {c2} {it2}. Всё верно?",
  reply_markup=builder.as_markup(),
  parse_mode="HTML"
 )


@router.callback_query(TradeCallback.filter())
async def handle_trade_callbacks(callback: types.CallbackQuery, callback_data: TradeCallback, get_user, save_db):
    u_init = get_user(callback_data.init_id)
    u_target = get_user(callback_data.target_id)

    # Подготавливаем ссылки (они понадобятся в обоих блоках ниже)
    name_i = u_init.get('first_name') or "Игрок 1"
    name_t = u_target.get('first_name') or "Игрок 2"
    link_init = f'<a href="tg://user?id={callback_data.init_id}">{html.escape(name_i)}</a>'
    link_target = f'<a href="tg://user?id={callback_data.target_id}">{html.escape(name_t)}</a>'

    # --- ЭТАП 1: Продавец нажал "Подтвердить" ---
    if callback_data.action == "confirm1":
        if callback.from_user.id != callback_data.init_id:
            return await callback.answer("Это не твой обмен! 😡", show_alert=True)

        data_confirm = callback_data.model_copy(update={"action": "confirm2"})
        data_cancel = callback_data.model_copy(update={"action": "cancel2"})

        builder = InlineKeyboardBuilder()
        builder.button(text="Обменяться 🔄", callback_data=data_confirm.pack())
        builder.button(text="Отменить ❌", callback_data=data_cancel.pack())
        builder.adjust(2)

        # ВОТ ТУТ ИМЕНА СТАНОВЯТСЯ ССЫЛКАМИ
        await callback.message.edit_text(
            f"<b>{link_target}</b>, пользователь <b>{link_init}</b> хочет передать "
            f"{callback_data.c1} {callback_data.it1} в обмен твои {callback_data.c2} {callback_data.it2}. "
            f"Подтвердить обмен?",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

    # --- ЭТАП 2: Финальное завершение ---
    elif callback_data.action == "confirm2":
        if callback.from_user.id != callback_data.target_id:
            return await callback.answer("Только покупатель может подтвердить! ✋", show_alert=True)

        inv_a = get_inv_dict(u_init)
        inv_b = get_inv_dict(u_target)
        if inv_a.get(callback_data.it1, 0) < callback_data.c1 or \
                inv_b.get(callback_data.it2, 0) < callback_data.c2:
            return await callback.message.edit_text("😭 Обмен сорвался! Предметов больше нет.")

        inv_a[callback_data.it1] -= callback_data.c1
        inv_b[callback_data.it1] = inv_b.get(callback_data.it1, 0) + callback_data.c1
        inv_b[callback_data.it2] -= callback_data.c2
        inv_a[callback_data.it2] = inv_a.get(callback_data.it2, 0) + callback_data.c2

        if inv_a[callback_data.it1] <= 0: inv_a.pop(callback_data.it1, None)
        if inv_b[callback_data.it2] <= 0: inv_b.pop(callback_data.it2, None)

        save_db()

        # В финальном сообщении ссылки тоже остаются
        await callback.message.edit_text(

            f"<b>{link_init}</b> {callback_data.c1} {callback_data.it1} 🔄 "
            f"{callback_data.c2} {callback_data.it2} <b>{link_target}</b>",
            parse_mode="HTML"
        )

    # --- ОТМЕНА ---
    elif "cancel" in callback_data.action:
        allowed_id = callback_data.init_id if "1" in callback_data.action else callback_data.target_id
        if callback.from_user.id != allowed_id:
            return await callback.answer("Ты не можешь это отменить! 🙄", show_alert=True)
        await callback.message.edit_text("Обмен был отменён! 🙊")