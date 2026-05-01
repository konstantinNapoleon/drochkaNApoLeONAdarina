from .pass_db import get_or_create_today_tasks, update_task_progress, add_peaches, get_pass_user


async def progress_task(user_id: int, task_id: str, amount: int = 1):
    """
    Добавляет прогресс к ежедневному заданию пользователя.
    Если нужного задания на сегодня нет — просто ничего не делает.
    """
    print(f"\n[DEBUG] progress_task вызван для user_id={user_id} с task_id='{task_id}'")
    tasks = await get_or_create_today_tasks(user_id)
    print(f"[DEBUG]  Задания на сегодня из БД: {tasks}")

    target_task = None
    for task in tasks:
        print(f"[DEBUG]  Проверяю задание: {task}")
        if task.get("task_id") == task_id:
            target_task = task
            print(f"[DEBUG]  Нашел нужное задание: {task}")
            break

    if not target_task:
        print(f"[DEBUG]  Задание с task_id='{task_id}' НЕ НАЙДЕНО. Выхожу.")
        return False

    if target_task.get("claimed"):
        print(f"[DEBUG]  Задание уже заклеймлено. Выхожу.")
        return False

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

    if is_completed:
        print("[DEBUG]  Задание ВЫПОЛНЕНО.")

    await update_task_progress(
        task_row_id=target_task["id"],
        progress=new_progress,
        is_completed=is_completed
    )
    print("[DEBUG]  Вызвал update_task_progress. Прогресс должен быть обновлен в БД.")
    return True


async def claim_task_reward(user_id: int, task_row_id: int):
  """
  Забирает награду за выполненное ежедневное задание.
  """
  from .pass_db import get_today_tasks, get_db_connection

  tasks = await get_today_tasks(user_id)
  target_task = None

  for task in tasks:
    if int(task["id"]) == int(task_row_id):
      target_task = task
      break

  if not target_task:
    return False, "Задание не найдено"

  if target_task.get("claimed"):
    return False, "Награда уже получена"

  if not target_task.get("is_completed"):
    return False, "Задание еще не выполнено"

  conn = get_db_connection()
  cursor = conn.cursor()

  try:
    cursor.execute("""
      UPDATE ivent_pass_daily_tasks
      SET claimed = TRUE
      WHERE id = %s
    """, (task_row_id,))
    conn.commit()
  finally:
    cursor.close()
    conn.close()

  # Получаем данные пользователя, чтобы проверить Ультра пасс
  pass_user = await get_pass_user(user_id)
  is_ultra = pass_user.get("is_ultra", False)

  reward = int(target_task.get("reward", 0))

  # Удваиваем награду, если есть пасс
  if is_ultra:
    reward *= 2

  new_peaches = await add_peaches(user_id, reward)

  return True, new_peaches