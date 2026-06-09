import html
import random
import string
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from items import GAME_ITEMS

router = Router()

BACKPACK_EMOJI = "🎒"
ITEMS_PER_PAGE = 10
# Временное хранилище для передачи (user_id: {bp_id, target_id})
PENDING_TRANSFERS = {}


def generate_backpack_id():
    parts = [
        ''.join(random.choices(string.hexdigits.lower(), k=8)),
        ''.join(random.choices(string.hexdigits.lower(), k=4)),
        ''.join(random.choices(string.hexdigits.lower(), k=4)),
        ''.join(random.choices(string.hexdigits.lower(), k=4)),
        ''.join(random.choices(string.hexdigits.lower(), k=12))
    ]
    return f"s_{'_'.join(parts)}"


def get_backpacks(user_data):
    if "backpacks" not in user_data:
        user_data["backpacks"] = {}
    if isinstance(user_data["backpacks"], list):
        user_data["backpacks"] = {}
    return user_data["backpacks"]


def get_active_backpack_id(user_data):
    return user_data.get("active_backpack_id")


def create_backpack(user_data):
    backpacks = get_backpacks(user_data)
    bp_id = generate_backpack_id()
    backpacks[bp_id] = {"name": f"Рюкзак #{len(backpacks) + 1}", "items": {}}
    if not user_data.get("active_backpack_id"):
        user_data["active_backpack_id"] = bp_id
    return bp_id


def get_backpack_by_id(user_data, bp_id):
    backpacks = get_backpacks(user_data)
    return backpacks.get(bp_id)


async def check_backpack_item(user_data, save_db, user_id):
    try:
        inv = user_data.get("inventory", {})
        bp_count = inv.get(BACKPACK_EMOJI, 0)
        backpacks = get_backpacks(user_data)

        if bp_count > len(backpacks):
            for _ in range(bp_count - len(backpacks)):
                create_backpack(user_data)
            await save_db(user_id, user_data)
            return True
        elif bp_count < len(backpacks):
            to_remove = []
            for bid, bdata in backpacks.items():
                if not bdata["items"] and len(to_remove) < len(backpacks) - bp_count:
                    to_remove.append(bid)
            for bid in to_remove:
                del backpacks[bid]
            if user_data.get("active_backpack_id") not in backpacks:
                user_data["active_backpack_id"] = list(backpacks.keys())[0] if backpacks else None
            await save_db(user_id, user_data)
            return True
        return False
    except Exception as e:
        print(f"Ошибка check_backpack_item: {e}")
        return False


async def transfer_backpack(user_data, target_user_data, bp_id, save_db, user_id, target_id):
    """Передаёт рюкзак со всем содержимым другому игроку"""
    backpacks = get_backpacks(user_data)
    target_backpacks = get_backpacks(target_user_data)

    if bp_id not in backpacks:
        return False, "Рюкзак не найден"

    backpack = backpacks[bp_id]
    items = backpack.get("items", {})
    items_count = sum(items.values())

    # Копируем рюкзак получателю
    new_bp_id = generate_backpack_id()
    target_backpacks[new_bp_id] = {
        "name": backpack["name"],
        "items": dict(items)
    }

    # Если активный рюкзак - ставим другой
    if user_data.get("active_backpack_id") == bp_id:
        remaining = [k for k in backpacks.keys() if k != bp_id]
        user_data["active_backpack_id"] = remaining[0] if remaining else None

    # Удаляем у отправителя
    del backpacks[bp_id]

    # Удаляем 1 🎒 из инвентаря отправителя
    inv = user_data.get("inventory", {})
    if inv.get(BACKPACK_EMOJI, 0) > 0:
        inv[BACKPACK_EMOJI] -= 1
        if inv[BACKPACK_EMOJI] <= 0:
            del inv[BACKPACK_EMOJI]

    # Добавляем 1 🎒 получателю
    target_inv = target_user_data.get("inventory", {})
    target_inv[BACKPACK_EMOJI] = target_inv.get(BACKPACK_EMOJI, 0) + 1

    await save_db(user_id, user_data)
    await save_db(target_id, target_user_data)

    return True, f"Передано {items_count} предметов"


# ========== КЛАВИАТУРЫ ==========

def get_backpacks_kb_with_view(user_data, page=0):
    backpacks = get_backpacks(user_data)
    active_id = get_active_backpack_id(user_data)
    bp_list = list(backpacks.items())

    total_pages = (len(bp_list) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if total_pages == 0:
        total_pages = 1
    if page < 0:
        page = 0
    if page >= total_pages:
        page = total_pages - 1

    builder = []
    start = page * ITEMS_PER_PAGE
    end = min(start + ITEMS_PER_PAGE, len(bp_list))

    for i, (bp_id, bp_data) in enumerate(bp_list[start:end], start + 1):
        is_active = bp_id == active_id
        mark = "✅ " if is_active else ""
        count = sum(bp_data["items"].values())
        status = f"[{count}]" if count > 0 else "[пуст]"

        builder.append([
            InlineKeyboardButton(
                text=f"{mark}{bp_data['name']} {status}",
                callback_data=f"bp_view_{bp_id}"
            )
        ])

    nav_row = []
    if total_pages > 1:
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"bp_page_{page - 1}"))
        nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="bp_page_info"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"bp_page_{page + 1}"))

    if nav_row:
        builder.append(nav_row)

    builder.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="bp_close")])

    return InlineKeyboardMarkup(inline_keyboard=builder)


def get_backpack_view_kb(bp_id, is_active=False):
    builder = [
        [InlineKeyboardButton(text="📥 Положить", callback_data=f"bp_put_{bp_id}")],
        [InlineKeyboardButton(text="📤 Взять", callback_data=f"bp_take_{bp_id}")],
        [InlineKeyboardButton(text="📤 Передать", callback_data=f"bp_transfer_{bp_id}")],
    ]
    if not is_active:
        builder.append([InlineKeyboardButton(text="✅ Активировать", callback_data=f"bp_activate_{bp_id}")])
    builder.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_backpacks")])
    builder.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="bp_close")])

    return InlineKeyboardMarkup(inline_keyboard=builder)


# ========== ХЕНДЛЕРЫ КОМАНД ==========

@router.message(Command("sklad", "рюкзаки", "bp", "склад"))
async def cmd_sklad(message: types.Message, get_user, save_db):
    try:
        user = await get_user(message.from_user.id, message.from_user.username)
        if not user:
            return await message.reply("❌ Ошибка.")

        backpacks = get_backpacks(user)
        inv = user.get("inventory", {})
        bp_count = inv.get(BACKPACK_EMOJI, 0)

        if bp_count > 0 and len(backpacks) < bp_count:
            for _ in range(bp_count - len(backpacks)):
                create_backpack(user)
            await save_db(message.from_user.id, user)
            backpacks = get_backpacks(user)

        if not backpacks:
            return await message.reply("❌ У тебя нет рюкзаков. Купи 🎒 в магазине!")

        await message.answer(
            "<b>🎒 Твои рюкзаки:</b>\n\n<i>Выбери рюкзак:</i>",
            reply_markup=get_backpacks_kb_with_view(user, 0),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка cmd_sklad: {e}")
        await message.reply("❌ Ошибка при загрузке рюкзаков.")


# ========== CALLBACK ХЕНДЛЕРЫ ==========

@router.callback_query(F.data.startswith("bp_view_"))
async def cb_bp_view(callback: types.CallbackQuery, get_user, save_db):
    try:
        bp_id = callback.data.split("_", 2)[2]
        user = await get_user(callback.from_user.id, callback.from_user.username)
        if not user:
            return await callback.answer("❌ Ошибка.", show_alert=True)

        backpack = get_backpack_by_id(user, bp_id)
        if not backpack:
            return await callback.answer("❌ Рюкзак не найден.", show_alert=True)

        items = backpack.get("items", {})
        active_id = get_active_backpack_id(user)
        is_active = bp_id == active_id

        text = f"🎒 <b>{backpack['name']}</b>\n\n"
        if is_active:
            text += "<i>🟢 Активный рюкзак</i>\n\n"

        if not items:
            text += "<i>Пусто</i>"
        else:
            items_list = []
            for item_emoji, count in items.items():
                item_name = GAME_ITEMS.get(item_emoji, {}).get("name", "???")
                items_list.append(f"{count} {item_emoji} <b>{item_name}</b>")
            text += "\n".join(items_list)

        await callback.message.edit_text(
            text,
            reply_markup=get_backpack_view_kb(bp_id, is_active),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка cb_bp_view: {e}")
        await callback.answer("❌ Ошибка.", show_alert=True)


@router.callback_query(F.data.startswith("bp_page_"))
async def cb_bp_page(callback: types.CallbackQuery, get_user, save_db):
    try:
        if callback.data == "bp_page_info":
            return await callback.answer()
        page = int(callback.data.split("_")[2])
        user = await get_user(callback.from_user.id, callback.from_user.username)
        if not user:
            return await callback.answer("❌ Ошибка.", show_alert=True)

        await callback.message.edit_text(
            "<b>🎒 Твои рюкзаки:</b>\n\n<i>Выбери рюкзак:</i>",
            reply_markup=get_backpacks_kb_with_view(user, page),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка cb_bp_page: {e}")
        await callback.answer("❌ Ошибка.", show_alert=True)


@router.callback_query(F.data == "bp_close")
async def cb_bp_close(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass


@router.callback_query(F.data == "back_to_backpacks")
async def cb_back_to_backpacks(callback: types.CallbackQuery, get_user, save_db):
    try:
        user = await get_user(callback.from_user.id, callback.from_user.username)
        if not user:
            return await callback.answer("❌ Ошибка.", show_alert=True)

        await callback.message.edit_text(
            "<b>🎒 Твои рюкзаки:</b>\n\n<i>Выбери рюкзак:</i>",
            reply_markup=get_backpacks_kb_with_view(user, 0),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка cb_back_to_backpacks: {e}")
        await callback.answer("❌ Ошибка.", show_alert=True)


@router.callback_query(F.data.startswith("bp_activate_"))
async def cb_bp_activate(callback: types.CallbackQuery, get_user, save_db):
    try:
        bp_id = callback.data.split("_", 2)[2]
        user = await get_user(callback.from_user.id, callback.from_user.username)
        if not user:
            return await callback.answer("❌ Ошибка.", show_alert=True)

        backpacks = get_backpacks(user)
        if bp_id not in backpacks:
            return await callback.answer("❌ Рюкзак не найден.", show_alert=True)

        user["active_backpack_id"] = bp_id
        await save_db(callback.from_user.id, user)

        await callback.answer(f"✅ Активен: {backpacks[bp_id]['name']}")

        backpack = backpacks[bp_id]
        items = backpack.get("items", {})
        is_active = True

        text = f"🎒 <b>{backpack['name']}</b>\n\n<i>🟢 Активный рюкзак</i>\n\n"
        if not items:
            text += "<i>Пусто</i>"
        else:
            items_list = []
            for item_emoji, count in items.items():
                item_name = GAME_ITEMS.get(item_emoji, {}).get("name", "???")
                items_list.append(f"{count} {item_emoji} <b>{item_name}</b>")
            text += "\n".join(items_list)

        await callback.message.edit_text(
            text,
            reply_markup=get_backpack_view_kb(bp_id, is_active),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка cb_bp_activate: {e}")
        await callback.answer("❌ Ошибка.", show_alert=True)


@router.callback_query(F.data.startswith("bp_put_"))
async def cb_bp_put(callback: types.CallbackQuery, get_user, save_db):
    try:
        bp_id = callback.data.split("_", 2)[2]
        await callback.message.edit_text(
            "<b>📥 Положить предмет в рюкзак</b>\n\n"
            "Напиши в чат:\n"
            "<code>юз 🎒 + 🏆 5</code>\n\n"
            "Или вернись назад:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↩️ Назад", callback_data=f"bp_view_{bp_id}")],
                [InlineKeyboardButton(text="❌ Закрыть", callback_data="bp_close")]
            ]),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка cb_bp_put: {e}")
        await callback.answer("❌ Ошибка.", show_alert=True)


@router.callback_query(F.data.startswith("bp_take_"))
async def cb_bp_take(callback: types.CallbackQuery, get_user, save_db):
    try:
        bp_id = callback.data.split("_", 2)[2]
        user = await get_user(callback.from_user.id, callback.from_user.username)
        if not user:
            return await callback.answer("❌ Ошибка.", show_alert=True)

        backpack = get_backpack_by_id(user, bp_id)
        if not backpack:
            return await callback.answer("❌ Рюкзак не найден.", show_alert=True)

        items = backpack.get("items", {})
        if not items:
            return await callback.answer("❌ Рюкзак пуст!", show_alert=True)

        builder = []
        for item_emoji, count in list(items.items())[:10]:
            item_name = GAME_ITEMS.get(item_emoji, {}).get("name", "???")
            builder.append([
                InlineKeyboardButton(
                    text=f"{count} {item_emoji} {item_name}",
                    callback_data=f"bp_take1_{bp_id}_{item_emoji}"
                )
            ])
        builder.append([InlineKeyboardButton(text="↩️ Назад", callback_data=f"bp_view_{bp_id}")])

        await callback.message.edit_text(
            f"📤 <b>Выбери предмет:</b>\n\n🎒 {backpack['name']}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=builder),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка cb_bp_take: {e}")
        await callback.answer("❌ Ошибка.", show_alert=True)


@router.callback_query(F.data.startswith("bp_take1_"))
async def cb_bp_take1(callback: types.CallbackQuery, get_user, save_db):
    try:
        parts = callback.data.split("_", 3)
        bp_id = parts[2]
        item_emoji = parts[3]

        user = await get_user(callback.from_user.id, callback.from_user.username)
        if not user:
            return await callback.answer("❌ Ошибка.", show_alert=True)

        backpack = get_backpack_by_id(user, bp_id)
        if not backpack:
            return await callback.answer("❌ Рюкзак не найден.", show_alert=True)

        if backpack["items"].get(item_emoji, 0) <= 0:
            return await callback.answer("❌ Предмета нет!", show_alert=True)

        if "inventory" not in user:
            user["inventory"] = {}
        user["inventory"][item_emoji] = user["inventory"].get(item_emoji, 0) + 1

        backpack["items"][item_emoji] -= 1
        if backpack["items"][item_emoji] <= 0:
            del backpack["items"][item_emoji]

        await save_db(callback.from_user.id, user)

        item_name = GAME_ITEMS[item_emoji].get("name", "Предмет")
        await callback.answer(f"✅ Взял 1 x {item_emoji} {item_name}")

        items = backpack.get("items", {})
        active_id = get_active_backpack_id(user)
        is_active = bp_id == active_id

        text = f"🎒 <b>{backpack['name']}</b>\n\n"
        if is_active:
            text += "<i>🟢 Активный рюкзак</i>\n\n"
        if not items:
            text += "<i>Пусто</i>"
        else:
            items_list = []
            for ie, count in items.items():
                inp = GAME_ITEMS.get(ie, {}).get("name", "???")
                items_list.append(f"{count} {ie} <b>{inp}</b>")
            text += "\n".join(items_list)

        await callback.message.edit_text(
            text,
            reply_markup=get_backpack_view_kb(bp_id, is_active),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка cb_bp_take1: {e}")
        await callback.answer("❌ Ошибка.", show_alert=True)


# ========== ПЕРЕДАЧА РЮКЗАКА ==========

@router.callback_query(F.data.startswith("bp_transfer_"))
async def cb_bp_transfer(callback: types.CallbackQuery, get_user, save_db):
    """Меню передачи рюкзака"""
    try:
        bp_id = callback.data.split("_", 2)[2]

        await callback.message.edit_text(
            "<b>📤 Передача рюкзака</b>\n\n"
            "Напиши:\n"
            "<code>/передатьрюкзак @username (ID)</code>\n\n"
            f"ID этого рюкзака: <code>{bp_id}</code>\n\n"
            "<i>Все предметы внутри будут переданы!</i>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↩️ Назад", callback_data=f"bp_view_{bp_id}")],
                [InlineKeyboardButton(text="❌ Закрыть", callback_data="bp_close")]
            ]),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка cb_bp_transfer: {e}")
        await callback.answer("❌ Ошибка.", show_alert=True)


@router.message(Command("передатьрюкзак", "givebp"))
async def cmd_give_backpack(message: types.Message, get_user, save_db, get_all_users):
    """Передать рюкзак другому игроку"""
    try:
        args = message.text.split(maxsplit=2)

        if len(args) < 3:
            return await message.reply(
                "❌ <b>Пример:</b>\n"
                "<code>/передатьрюкзак @username s_xxx</code>\n\n"
                "ID узнай в /склад",
                parse_mode="HTML"
            )

        target_username = args[1].replace("@", "").lower()
        bp_id = args[2].strip()

        user = await get_user(message.from_user.id, message.from_user.username)
        if not user:
            return await message.reply("❌ Ошибка.")

        backpacks = get_backpacks(user)
        if bp_id not in backpacks:
            return await message.reply("❌ Рюкзак не найден.")

        backpack = backpacks[bp_id]
        items_count = sum(backpack["items"].values())

        # Поиск получателя
        all_users = await get_all_users()

        target_user = None
        target_id = None
        for uid, udata in all_users.items():
            uname = udata.get("username", "") or ""
            if uname.lower() == target_username:
                target_user = udata
                target_id = uid
                break

        if not target_user:
            return await message.reply(f"❌ Пользователь @{target_username} не найден.")

        if str(target_id) == str(message.from_user.id):
            return await message.reply("❌ Нельзя передать самому себе.")

        # Сохраняем в временное хранилище
        user_id = str(message.from_user.id)
        PENDING_TRANSFERS[user_id] = {
            "bp_id": bp_id,
            "target_id": target_id,
            "target_name": target_username,
            "items": items_count
        }

        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"bpt_confirm:{user_id}")
        )
        builder.row(
            types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"bpt_cancel:{user_id}")
        )

        await message.reply(
            f"🎒 <b>Передача рюкзака</b>\n\n"
            f"📦 <b>{backpack['name']}</b>\n"
            f"📊 Предметов: {items_count}\n"
            f"👤 Кому: @{target_username}\n\n"
            f"<i>Все предметы внутри будут переданы!</i>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка cmd_give_backpack: {e}")
        await message.reply(f"❌ Ошибка при передаче: {e}")


@router.callback_query(F.data.startswith("bpt_confirm:"))
async def cb_transfer_confirm(callback: types.CallbackQuery, get_user, save_db):
    """Подтверждение передачи"""
    try:
        user_id = callback.data.split(":")[1]

        if user_id != str(callback.from_user.id):
            return await callback.answer("❌ Это не ваша передача!", show_alert=True)

        transfer = PENDING_TRANSFERS.get(user_id)
        if not transfer:
            return await callback.answer("❌ Время вышло! Начните заново.", show_alert=True)

        bp_id = transfer["bp_id"]
        target_id = transfer["target_id"]

        user = await get_user(callback.from_user.id, callback.from_user.username)
        if not user:
            return await callback.answer("❌ Ошибка.", show_alert=True)

        backpacks = get_backpacks(user)
        if bp_id not in backpacks:
            return await callback.answer("❌ Рюкзак не найден.", show_alert=True)

        target_user = await get_user(target_id)
        if not target_user:
            return await callback.answer("❌ Получатель не найден.", show_alert=True)

        success, msg = await transfer_backpack(user, target_user, bp_id, save_db, callback.from_user.id, target_id)

        # Очищаем хранилище
        del PENDING_TRANSFERS[user_id]

        if success:
            await callback.answer(f"✅ {msg}")
            await callback.message.edit_text(f"✅ <b>Рюкзак передан!</b>\n\n{msg}", parse_mode="HTML")

            try:
                await callback.message.bot.send_message(
                    target_id,
                    f"🎁 <b>Тебе передали рюкзак!</b>\n\n{msg}\n\nИспользуй /склад чтобы посмотреть.",
                    parse_mode="HTML"
                )
            except:
                pass
        else:
            await callback.answer(f"❌ {msg}", show_alert=True)
            await callback.message.edit_text(f"❌ <b>Ошибка:</b> {msg}", parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка cb_transfer_confirm: {e}")
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@router.callback_query(F.data.startswith("bpt_cancel:"))
async def cb_transfer_cancel(callback: types.CallbackQuery):
    """Отмена передачи"""
    try:
        user_id = callback.data.split(":")[1]
        if user_id in PENDING_TRANSFERS:
            del PENDING_TRANSFERS[user_id]
        await callback.message.edit_text("❌ <b>Передача отменена</b>", parse_mode="HTML")
    except:
        pass


# ========== ЮЗ 🎒 ==========

@router.message(F.text.lower() == "юз 🎒")
async def use_backpack_show(message: types.Message, get_user, save_db):
    try:
        user = await get_user(message.from_user.id, message.from_user.username)
        if not user:
            return await message.reply("❌ Ошибка.")

        backpacks = get_backpacks(user)
        active_id = get_active_backpack_id(user)

        if not active_id or active_id not in backpacks:
            return await message.reply("❌ Нет активного рюкзака. Используй /склад")

        backpack = backpacks[active_id]
        items = backpack.get("items", {})

        if not items:
            return await message.reply(
                f"🎒 <b>{backpack['name']}</b> [пуст]\n\n"
                f"<i>Положи: <code>юз 🎒 + 🏆 5</code></i>",
                parse_mode="HTML"
            )

        items_list = [f"{count} {emoji}" for emoji, count in items.items()]
        text = f"🎒 <b>Содержимое {backpack['name']}</b>\n\n{', '.join(items_list)}"
        await message.reply(text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка use_backpack_show: {e}")
        await message.reply("❌ Ошибка.")


@router.message(F.text.lower().startswith("юз 🎒 + "))
async def use_backpack_put(message: types.Message, get_user, save_db):
    try:
        parts = message.text.split(" + ", 1)[1].strip().split()
    except:
        return await message.reply("❌ Ошибка команды.")

    if not parts:
        return await message.reply("❌ Укажи предмет.")

    item_emoji = parts[0]
    quantity = 1

    if len(parts) > 1:
        try:
            quantity = int(parts[1])
        except:
            return await message.reply("❌ Неверное количество.")

    if item_emoji not in GAME_ITEMS:
        return await message.reply("❌ Такого предмета нет.")

    if item_emoji == BACKPACK_EMOJI:
        return await message.reply("❌ Нельзя положить рюкзак в рюкзак!")

    user = await get_user(message.from_user.id, message.from_user.username)
    if not user:
        return await message.reply("❌ Ошибка.")

    inv = user.get("inventory", {})
    available = inv.get(item_emoji, 0)

    if available <= 0:
        return await message.reply(f"❌ У тебя нет {item_emoji}.")

    if quantity > available:
        return await message.reply(f"❌ У тебя только {available} {item_emoji}.")

    backpacks = get_backpacks(user)
    active_id = get_active_backpack_id(user)

    if not active_id or active_id not in backpacks:
        return await message.reply("❌ Нет активного рюкзака.")

    backpack = backpacks[active_id]

    inv[item_emoji] -= quantity
    if inv[item_emoji] <= 0:
        del inv[item_emoji]

    backpack["items"][item_emoji] = backpack["items"].get(item_emoji, 0) + quantity

    await save_db(message.from_user.id, user)

    item_name = GAME_ITEMS[item_emoji].get("name", "Предмет")
    await message.reply(
        f"✅ <b>Положил в рюкзак {quantity} x {item_emoji} {item_name}!</b>",
        parse_mode="HTML"
    )


@router.message(F.text.lower().startswith("юз 🎒 - "))
async def use_backpack_take(message: types.Message, get_user, save_db):
    try:
        parts = message.text.split(" - ", 1)[1].strip().split()
    except:
        return await message.reply("❌ Ошибка команды.")

    if not parts:
        return await message.reply("❌ Укажи предмет.")

    item_emoji = parts[0]
    quantity = 1

    if len(parts) > 1:
        try:
            quantity = int(parts[1])
        except:
            return await message.reply("❌ Неверное количество.")

    user = await get_user(message.from_user.id, message.from_user.username)
    if not user:
        return await message.reply("❌ Ошибка.")

    backpacks = get_backpacks(user)
    active_id = get_active_backpack_id(user)

    if not active_id or active_id not in backpacks:
        return await message.reply("❌ Нет активного рюкзака.")

    backpack = backpacks[active_id]
    available = backpack["items"].get(item_emoji, 0)

    if available <= 0:
        return await message.reply(f"❌ В рюкзаке нет {item_emoji}.")

    if quantity > available:
        return await message.reply(f"❌ В рюкзаке только {available} {item_emoji}.")

    if "inventory" not in user:
        user["inventory"] = {}
    user["inventory"][item_emoji] = user["inventory"].get(item_emoji, 0) + quantity

    backpack["items"][item_emoji] -= quantity
    if backpack["items"][item_emoji] <= 0:
        del backpack["items"][item_emoji]

    await save_db(message.from_user.id, user)

    item_name = GAME_ITEMS[item_emoji].get("name", "Предмет")
    await message.reply(
        f"✅ <b>Взял {quantity} x {item_emoji} {item_name}!</b>",
        parse_mode="HTML"
    )


# ========== ХЕЛП ==========

@router.message(F.text.lower() == "юз 🎒 хелп")
async def backpack_help(message: types.Message):
    text = (
        "<b>🎒 Рюкзаки (Склад):</b>\n\n"
        "<b>Команды:</b>\n"
        "<code>/склад</code> — список рюкзаков\n"
        "<code>юз 🎒</code> — содержимое активного\n"
        "<code>юз 🎒 + 🏆 5</code> — положить 5 шт\n"
        "<code>юз 🎒 - 🏆 3</code> — взять 3 шт\n"
        "<code>/передатьрюкзак @user (ID)</code> — передать\n\n"
        "<i>Каждый 🎒 в инвентаре = отдельный склад</i>"
    )
    await message.reply(text, parse_mode="HTML")