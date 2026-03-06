from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from items import GAME_ITEMS

router = Router()

# Кастомные ответы на использование
USE_RESPONSES = {
    "⚽": "Мячик для футбола, осторожно мошенники."
}


# Используем твою функцию из основного кода
def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        inv = {}
        user["inventory"] = inv
    return inv


async def process_item_use(message: types.Message, item_emoji: str, get_user, save_db):
    if item_emoji not in GAME_ITEMS:
        return await message.reply("❌ Такого предмета не существует.")

    user = get_user(message.from_user.id)
    inv_dict = ensure_inv_dict(user)

    # Проверяем, есть ли предмет у пользователя в словаре инвентаря
    item_count = inv_dict.get(item_emoji, 0)

    if item_count <= 0:
        return await message.reply("❌ У тебя нету такого предмета.")

    item_name = GAME_ITEMS[item_emoji].get("name", "Неизвестный предмет")

    # Если нужно забирать предмет при использовании, раскомментируй эти строки:
    # inv_dict[item_emoji] -= 1
    # if inv_dict[item_emoji] <= 0:
    #   del inv_dict[item_emoji]
    # save_db()

    response = USE_RESPONSES.get(item_emoji, f"Вы успешно использовали {html.escape(item_name)}.")
    await message.reply(response, parse_mode="HTML")


# --- ОБРАБОТЧИКИ ---

@router.message(Command("use"))
async def cmd_use(message: types.Message, get_user, save_db):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("Укажи предмет. Пример: /use ⚽")

    await process_item_use(message, args[1].strip(), get_user, save_db)


@router.message(F.text.lower().startswith("юз "))
async def text_use(message: types.Message, get_user, save_db):
    item_emoji = message.text[3:].strip()
    if not item_emoji:
        return await message.reply("Укажи предмет. Пример: юз ⚽")

    await process_item_use(message, item_emoji, get_user, save_db)