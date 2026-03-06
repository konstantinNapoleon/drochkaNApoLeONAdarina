from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from items import GAME_ITEMS

router = Router()

# Кастомные ответы на использование
USE_RESPONSES = {
    "⚽": "Мячик для футбола, осторожно мошенники."
}


async def process_item_use(message: Message, item_emoji: str):
    if item_emoji not in GAME_ITEMS:
        return await message.reply("❌ Такого предмета не существует.")

    item_name = GAME_ITEMS[item_emoji]["name"]
    response = USE_RESPONSES.get(item_emoji, f"Вы успешно использовали {item_name}.")
    await message.reply(response)


@router.message(Command("use"))
async def cmd_use(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("Укажи предмет. Пример: /use ⚽")

    await process_item_use(message, args[1].strip())


@router.message(F.text.lower().startswith("юз "))
async def text_use(message: Message):
    item_emoji = message.text[3:].strip()
    if not item_emoji:
        return await message.reply("Укажи предмет. Пример: юз ⚽")

    await process_item_use(message, item_emoji)