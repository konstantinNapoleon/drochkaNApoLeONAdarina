
from .pass_db import get_or_create_today_tasks, update_task_progress, add_cherries, get_pass_user
# --- ДОБАВЛЕННЫЙ ИМПОРТ ---
from .pass_data import PASS_TIER_ULTRA, PASS_TIER_MEGA



async def progress_task(user_id: int, task_id: str, amount: int = 1):
    """
    Добавляет прогресс к ежедневному заданию.
    Если задание выполнено и включен авто-сбор, забирает награду.
    """
    print(f"\n[DEBUG] progress_task вызван для user_id={user_id} с task_id='{task_id}'")
    tasks = await get_or_create_today_tasks(user_id)
    print(f"[DEBUG]  Задания на сегодня из БД: {tasks}")

    target_task = None
    for task in tasks:
        # Добавил проверку на 'claimed', чтобы не трогать уже собранные
        if task.get("task_id") == task_id and not task.get("claimed"):
            target_task = task
            print(f"[DEBUG]  Нашел нужное задание: {task}")
            break

    if not target_task:
        print(f"[DEBUG]  Активное задание с task_id='{task_id}' НЕ НАЙДЕНО. Выхожу.")
        return False

    # Этот блок остается без изменений
    current = int(target_task.get("progress", 0))
    target = int(target_task.get("target", 1))
    if current >= target:
        print(f"[DEBUG]  Прогресс уже 100%. Выхожу.")
        return False
    new_progress = current + amount
    if new_progress > target:
        new_progress = target
    print(f"[DEBUG]  Новый прогресс: {new_progress}/{target}")
    is_completed = new_progress >= target

    await update_task_progress(
        task_row_id=target_task["id"],
        progress=new_progress,
        is_completed=is_completed
    )
    print("[DEBUG]  Прогресс обновлен в БД.")

    # --- НОВАЯ ЛОГИКА АВТО-СБОРА ---
    if is_completed:
        print("[DEBUG]  Задание ВЫПОЛНЕНО. Проверяю условия для авто-сбора.")
        pass_user = await get_pass_user(user_id)
        # Проверяем, что у юзера премиум и включена настройка
        if pass_user.get("auto_claim_enabled") and pass_user.get("pass_tier", 0) > 0:
            print("[DEBUG]  Авто-сбор включен! Вызываю claim_task_reward...")
            await claim_task_reward(user_id, target_task["id"])
            print(f"[DEBUG]  Авто-сбор для задания {target_task['id']} выполнен.")

    return True


async def claim_task_reward(user_id: int, task_row_id: int):
  """
  Забирает награду за выполненное ежедневное задание.
  ИЗМЕНЕНО: использует pass_tier для расчета множителя x2/x3.
  """
  from .pass_db import get_today_tasks, get_db_connection

  tasks = await get_today_tasks(user_id)
  target_task = None
  for task in tasks:
    if int(task["id"]) == int(task_row_id):
      target_task = task
      break

  if not target_task or target_task.get("claimed") or not target_task.get("is_completed"):
    return False, "Награда уже получена или задание не выполнено"

  conn = get_db_connection()
  cursor = conn.cursor()
  try:
      cursor.execute("UPDATE ivent_pass_daily_tasks SET claimed = TRUE WHERE id = %s", (task_row_id,))
      conn.commit()
  finally:
      cursor.close()
      conn.close()

      # --- НОВАЯ ЛОГИКА НАЧИСЛЕНИЯ НАГРАДЫ ---
  pass_user = await get_pass_user(user_id)
  pass_tier = pass_user.get("pass_tier", 0)
  reward = int(target_task.get("reward", 0))

  if pass_tier == PASS_TIER_ULTRA:
      reward *= 2
  elif pass_tier == PASS_TIER_MEGA:
      reward *= 3

  new_cherries_total = await add_cherries(user_id, reward)
  return True, new_cherries_total

