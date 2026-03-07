import html
from aiogram import Router, types, F
from aiogram.filters import Command

router = Router()

FARMCOIN = "💰"


@router.message(Command("si"))
async def cmd_inventory_grid(message: types.Message, get_user, save_db):
    user = get_user(message.from_user.id)
    inv_data = user.get('inventory', {})

    # --- КОНВЕРТАЦИЯ (из списка в словарь, если нужно) ---
    if isinstance(inv_data, list):
        new_inv = {}
        for item in inv_data:
            new_inv[item] = new_inv.get(item, 0) + 1
        inv_data = new_inv
        user['inventory'] = inv_data
        save_db()  # Сохраняем новый формат
    elif not isinstance(inv_data, dict):
        inv_data = {}

    # --- ПОЛУЧАЕМ ДАННЫЕ ---
    farmcoins = inv_data.get(FARMCOIN, 0)

    # Собираем остальные предметы (кроме монет)
    counts = {emoji: count for emoji, count in inv_data.items() if emoji != FARMCOIN and count > 0}

    # Собираем всё для отображения: сначала 💰, потом остальное
    all_items = []
    if farmcoins > 0:
        all_items.append((farmcoins, FARMCOIN))

    for emoji, count in counts.items():
        all_items.append((count, emoji))

    if not all_items:
        return await message.answer("🎒 Твой инвентарь пуст.")

    # --- РЕНДЕР СЕТКИ (Твой стиль) ---
    formatted_items = []
    # --- РЕНДЕР СЕТКИ (С выравниванием) ---
    # Определяем ширину поля под число.
    # 7 символов хватит для чисел до 9 999 999.
    NUM_WIDTH = 5

    formatted_items = []
    for count, emoji in all_items:
        # f"{str(count):>{NUM_WIDTH}}" — выравнивает число по правому краю
        # Добавляем пробел и эмодзи после числа
        item_str = f"{str(count):>{NUM_WIDTH}} {emoji}"
        formatted_items.append(item_str)

    # Разбиваем на строки по 3 предмета
    rows = []
    for i in range(0, len(formatted_items), 3):
        # Соединяем элементы строки через разделитель "|"
        # Благодаря фиксированной ширине NUM_WIDTH, палочки будут стоять ровно друг под другом
        rows.append(" | ".join(formatted_items[i:i + 3]))

    inventory_render = "\n".join(rows)

    # <pre> — обязателен для работы выравнивания
    response = f"<pre>{html.escape(inventory_render)}</pre>"
    await message.answer(response, parse_mode="HTML")


 #dfff



