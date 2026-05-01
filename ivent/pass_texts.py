from ivent.pass_data import (
    SEASON_TITLE,
    SEASON_DESCRIPTION,
    ULTRA_PASS_DAILY_BONUS,
    ULTRA_PASS_COST,
    DAILY_BONUS_REWARD,
)


def build_main_menu_text(user_level: int, is_ultra: bool, days_left: int) -> str:
    pass_type = "Ультра" if is_ultra else "Обычный"

    return (
        f"{SEASON_TITLE}\n\n"
        f"— Твой уровень: {user_level}\n"
        f"— Пропуск: {pass_type}\n"
        f"— До окончания сезона: {days_left} д.\n\n"
        f"{SEASON_DESCRIPTION}"
    )



def build_tasks_text(tasks: list, hours_left_text: str, is_ultra: bool) -> str: # Добавляем is_ultra
  lines = ["📋 <b>Текущие ежедневные задания:</b>\n"]

  for idx, task in enumerate(tasks, start=1):
    if task.get("claimed"):
      status = "🏆"
    elif task.get("is_completed"):
      status = "✅"
    else:
      status = "❌"

    progress = task.get("progress", 0)
    target = task.get("target", 1)
    reward = task.get("reward", 0)

    # Удваиваем награду для Ультра пасса
    if is_ultra:
      reward *= 2

    lines.append(
      f"[{idx}] {task['text']} ({status})\n"
      f"Прогресс: {progress}/{target}\n"
      f"Награда: {reward} 🍑\n"
    )

  lines.append(f"Обновление через {hours_left_text}")
  return "\n".join(lines)


def build_bonus_text(already_claimed: bool, is_ultra: bool) -> str:
    if already_claimed:
        return (
            "🎁 <b>Ежедневный бонус</b>\n\n"
            "Ты уже забрал бонус сегодня.\n"
            "Возвращайся завтра за новой порцией 🍑"
        )

    bonus_text = f"<b>{DAILY_BONUS_REWARD}</b> 🍑"
    if is_ultra:
        bonus_text += f" (+{ULTRA_PASS_DAILY_BONUS} 🍑 за Ультра пропуск)"

    return (
        "🎁 <b>Ежедневный бонус</b>\n\n"
        "Нажми кнопку ниже, чтобы забрать ежедневный бонус:\n"
        f"{bonus_text}"
    )


def build_info_text() -> str:
    return (
        "ℹ️ <b>Информация о пропуске</b>\n\n"
        "— За каждый уровень нужно 150 🍑\n"
        "— Всего в сезоне 10 уровней\n"
        "— Каждый день выдается 3 случайных задания\n"
        f"— Также доступен ежедневный бонус {DAILY_BONUS_REWARD} 🍑\n\n"
        "💠 <b>Преимущества Ультра пропуска:</b>\n"
        f"— Стоимость: {ULTRA_PASS_COST} 🪙\n"
        "— В 2 раза больше 🍑 за ежедневные задания\n"
        f"— Дополнительный ежедневный бонус: +{ULTRA_PASS_DAILY_BONUS} 🍑\n"
        "— Эксклюзивные награды за каждый уровень"
    )
