# pass_texts.py

# Импортируем все необходимые переменные из твоей новой конфигурации
from ivent.pass_data import (
  SEASON_TITLE,
  SEASON_DESCRIPTION,
  ULTRA_PASS_DAILY_BONUS,
  ULTRA_PASS_COST,
  DAILY_BONUS_REWARD,
  SECTORS,
  MAX_LEVEL,
  CHERRIES_PER_LEVEL,
  CHERRY_EMOJI,
)

# Новая вспомогательная функция для определения сектора пользователя по его уровню
def get_sector_name(user_level: int) -> str:
  """Определяет название сектора по уровню пользователя."""
  if user_level == 0:
    return "Не определена"
  for sector_id, sector_data in SECTORS.items():
    if user_level in sector_data['levels']:
      return f"{sector_id}: {sector_data['name']}"
  # Если уровень пользователя больше максимального, он в последнем секторе
  if user_level >= max(SECTORS['A']['levels']):
    return f"A: {SECTORS['A']['name']}"
  return "Неизвестно"

# Обновленный текст главного меню
def build_main_menu_text(user_level: int, is_ultra: bool, days_left: int) -> str:
  pass_type = "Ультра" if is_ultra else "Обычный"
  sector_name = get_sector_name(user_level)

  return (
    f"<b>{SEASON_TITLE}</b>\n\n"
    f"— Твой этап: {user_level}\n"
    f"— Твоя Секта: {sector_name}\n"
    f"— Пропуск: {pass_type}\n"
    f"— До окончания: {days_left} д.\n\n"
    f"{SEASON_DESCRIPTION}"
  )

# Обновленный текст заданий (замена эмодзи)
def build_tasks_text(tasks: list, hours_left_text: str, is_ultra: bool) -> str:
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

    if is_ultra:
      reward *= 2

    lines.append(
      f"[{idx}] {task['text']} ({status})\n"
      f"Прогресс: {progress}/{target}\n"
      f"Награда: {reward} {CHERRY_EMOJI}\n"
    )

  lines.append(f"Обновление через {hours_left_text}")
  return "\n".join(lines)

# Обновленный текст бонуса (замена эмодзи и значений)
def build_bonus_text(already_claimed: bool, is_ultra: bool) -> str:
  if already_claimed:
    return (
      "🎁 <b>Ежедневный бонус</b>\n\n"
      "Ты уже забрал бонус сегодня.\n"
      f"Возвращайся завтра за новой порцией {CHERRY_EMOJI}"
    )

  bonus_text = f"<b>{DAILY_BONUS_REWARD}</b> {CHERRY_EMOJI}"
  if is_ultra:
    bonus_text += f" (+{ULTRA_PASS_DAILY_BONUS} {CHERRY_EMOJI} за Ультра пропуск)"

  return (
    "🎁 <b>Ежедневный бонус</b>\n\n"
    "Нажми кнопку ниже, чтобы забрать ежедневный бонус:\n"
    f"{bonus_text}"
  )

# Полностью переписанный текст информации
def build_info_text() -> str:
  return (
    "ℹ️ <b>Информация о пропуске</b>\n\n"
    f"— За каждый этап нужно {CHERRIES_PER_LEVEL} {CHERRY_EMOJI}\n"
    f"— Всего в сезоне {MAX_LEVEL} этапов, разделенных на 4 сектора\n"
    "— Каждый день выдается 3 случайных задания\n"
    f"— Также доступен ежедневный бонус {DAILY_BONUS_REWARD} {CHERRY_EMOJI}\n\n"
    "💠 <b>Преимущества Ультра пропуска:</b>\n"
    f"— Стоимость: {ULTRA_PASS_COST} 🪙\n"
    f"— В 2 раза больше {CHERRY_EMOJI} за ежедневные задания\n"
    f"— Дополнительный ежедневный бонус: +{ULTRA_PASS_DAILY_BONUS} {CHERRY_EMOJI}\n"
    "— Эксклюзивные награды за каждый этап"
  )

