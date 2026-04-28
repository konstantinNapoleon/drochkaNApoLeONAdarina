import math
import datetime

from ivent.pass_data import PEACHES_PER_LEVEL, MAX_LEVEL, PASS_LEVELS, SEASON_END
from items import GAME_ITEMS


def get_user_level(peaches: int) -> int:
    if peaches <= 0:
        return 0
    return min(MAX_LEVEL, peaches // PEACHES_PER_LEVEL)


def get_level_required_peaches(level: int) -> int:
    return level * PEACHES_PER_LEVEL


def get_level_progress(peaches: int, level: int):
    """
    Возвращает прогресс внутри конкретного уровня.
    Например:
    level=4 -> диапазон 451-600 при шаге 150
    """
    if level <= 1:
        prev_required = 0
    else:
        prev_required = (level - 1) * PEACHES_PER_LEVEL

    current_required = level * PEACHES_PER_LEVEL
    current_progress = max(0, peaches - prev_required)
    need_for_level = current_required - prev_required

    if current_progress > need_for_level:
        current_progress = need_for_level

    return current_progress, need_for_level


def build_progress_bar(current: int, total: int, size: int = 10) -> str:
    if total <= 0:
        return "▱" * size

    filled = math.floor((current / total) * size)
    if filled > size:
        filled = size

    return "▰" * filled + "▱" * (size - filled)


def format_rewards(rewards: dict) -> str:
    lines = []

    for emoji, amount in rewards.items():
        item_data = GAME_ITEMS.get(emoji, {})
        item_name = item_data.get("name", "Неизвестный предмет")

        if amount == 1:
            lines.append(f"{emoji} <b>{item_name}</b>")
        else:
            lines.append(f"{emoji} <b>{item_name}</b> x{amount}")

    return "\n".join(lines)


def get_level_status(peaches: int, level: int, claimed_levels: list[int]) -> str:
    required = get_level_required_peaches(level)

    if level in claimed_levels:
        return "получено ✅"
    if peaches >= required:
        return "ожидает сбор"
    return "не достигнуто"


def get_days_left() -> int:
    now = datetime.datetime.now()
    delta = SEASON_END - now
    return max(0, delta.days)


def get_hours_left_until_reset() -> str:
    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=1)
    next_reset = datetime.datetime(
        tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0
    )
    delta = next_reset - now
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return f"{hours}ч {minutes}м"


def build_stage_text(level: int, peaches: int, claimed_levels: list[int], is_ultra: bool) -> str:
    level_data = PASS_LEVELS[level]

    # Собираем награды в один словарь, добавляя Ультра-награды, если пропуск активен
    rewards_to_show = level_data.get("rewards", {}).copy()
    if is_ultra:
        ultra_rewards = level_data.get("ultra_rewards", {})
        for emoji, amount in ultra_rewards.items():
            rewards_to_show[emoji] = rewards_to_show.get(emoji, 0) + amount

    rewards_text = format_rewards(rewards_to_show)
    status = get_level_status(peaches, level, claimed_levels)
    current, total = get_level_progress(peaches, level)
    bar = build_progress_bar(current, total)

    return (
        f"📦 <b>Боевой Пропуск | Уровень {level}</b>\n\n"
        f"<b>Награда:</b>\n"
        f"{rewards_text}\n\n"
        f"Прогресс: {bar} {current}/{total}\n\n"
        f"Статус: <b>{status}</b>"
    )
