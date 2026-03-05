import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties # Для установки parse_mode по умолчанию
from dotenv import load_dotenv
load_dotenv()
# --- Импорты роутеров ---
# Убедись, что эти файлы существуют в папках `handlers` и `inventory`,
# и что в каждой из этих папок есть пустой файл `__init__.py`.
# Каждый из этих файлов роутеров должен содержать строку `router = Router()` в начале.
from handlers.start import router as start_router
from handlers.droch import router as droch_router
from handlers.ferma import router as ferma_router
from handlers.shop import router as shop_router
from inventory.commands import router as inventory_router # Роутер из новой папки inventory
from handlers.oil import router as oil_router
from handlers.itemgive import router as itemgive_router
from handlers.bonus import router as bonus_router
from handlers.id import router as id_router
from handlers.vidacha import router as vidacha_router
from inventory.inventar import router as inventar_router
from tools.admin import router as admin_router

from farm.topdrochek import router as topdrochek_router
from tools.reklama import router as reklama_router
from dataIT.bonuscode import router as bonuscode_router


# --- НАСТРОЙКИ БОТА ---
# !!! ВАЖНО: Замени "ТВОЙ_ТОКЕН" на токен твоего бота, полученный от BotFather !!!
# Вместо TOKEN = "1234567890"
TOKEN = os.getenv("BOT_TOKEN")

# Вместо DB_FILE = "database.json"
DB_FILE = os.getenv("DB_FILE", "database.json")

# Настройка логирования для вывода информации в консоль
# Показывает время, уровень лога (INFO, WARNING, ERROR), имя логгера и сообщение
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__) # Получаем логгер для текущего файла

# --- ГЛОБАЛЬНАЯ ПЕРЕМЕННАЯ ДЛЯ ДАННЫХ БАЗЫ ---
# В этой переменной будет храниться вся загруженная информация о пользователях
db_data = {}

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ (JSON-файл) ---

def load_db():
  """
  Загружает данные пользователей из JSON-файла в глобальную переменную `db_data`.
  Если файл не найден или поврежден, инициализирует пустую базу данных.
  """
  global db_data # Объявляем, что используем глобальную переменную db_data
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r", encoding="utf-8") as f:
        db_data = json.load(f)
      logger.info(f"База данных '{DB_FILE}' успешно загружена.")
    except json.JSONDecodeError:
      logger.warning(
        f"Ошибка чтения JSON из '{DB_FILE}'. Файл поврежден или пуст. "
        "Инициализирована пустая база данных."
      )
      db_data = {} # Если JSON поврежден, начинаем с чистого листа
    except Exception as e:
      logger.error(f"Неизвестная ошибка при загрузке '{DB_FILE}': {e}", exc_info=True)
      db_data = {}
  else:
    logger.info(f"Файл базы данных '{DB_FILE}' не найден. Создана новая база данных.")
    db_data = {} # Если файла нет, создаем пустую базу

def save_db():
  """
  Сохраняет текущие данные пользователей из `db_data` в JSON-файл.
  """
  try:
    with open(DB_FILE, "w", encoding="utf-8") as f:
      json.dump(db_data, f, ensure_ascii=False, indent=4)
    logger.debug(f"База данных '{DB_FILE}' успешно сохранена.")
  except Exception as e:
    logger.error(f"Ошибка при сохранении '{DB_FILE}': {e}", exc_info=True)


def get_user(user_id, username=None):
  uid = str(user_id)
  if uid not in db_data:
    db_data[uid] = {
      "balance": 0,
      "inventory": [],
      "masturbations_count": 0,
      "username": username  # Сохраняем ник при создании
    }
  else:
    # ОБЯЗАТЕЛЬНО: Если ник пришел, обновляем его в базе
    if username:
      db_data[uid]["username"] = username

  save_db()  # Сохраняем в файл users.json
  return db_data[uid]
def get_all_users():
  return db_data

# --- ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА БОТА ---

async def main():
  """
  Основная асинхронная функция, которая запускает бота.
  """
  # 1. Загружаем базу данных при старте бота
  load_db()

  # 2. Инициализация бота и диспетчера
  # default=DefaultBotProperties(parse_mode="HTML") устанавливает HTML-режим по умолчанию
  bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
  dp = Dispatcher()

  # 3. Передаем функции базы данных в контекст диспетчера.
  # Aiogram будет автоматически передавать их в обработчики,
  # если функция обработчика имеет аргументы с такими же именами (например, `get_user`, `save_db`).
  dp["get_user"] = get_user
  dp["save_db"] = save_db

  # 4. Подключение всех роутеров к диспетчеру
  # Порядок подключения может быть важен, если есть пересекающиеся команды.
  # Обычно сначала подключают более специфичные, потом общие.
  dp.include_router(start_router)
  dp.include_router(droch_router)

  dp.include_router(shop_router)
  dp.include_router(inventory_router) # Роутер инвентаря
  dp.include_router(oil_router)
  dp.include_router(itemgive_router)
  dp.include_router(bonus_router)
  dp.include_router(id_router)
  dp.include_router(vidacha_router)
  dp.include_router(inventar_router)
  dp.include_router(admin_router)
  dp.include_router(ferma_router)
  dp.include_router(topdrochek_router)
  dp.include_router(reklama_router)
  dp.include_router(bonuscode_router)


  # 5. Удаление ожидающих обновлений
  # Это гарантирует, что бот не будет обрабатывать старые сообщения,
  # пока он был выключен.
  await bot.delete_webhook(drop_pending_updates=True)
  logger.info("🚀 БОТ ЗАПУЩЕН!")



  # 6. Запуск поллинга (получения обновлений)
  # Бот начнет слушать входящие сообщения.
  await dp.start_polling(
    bot,
    get_user=get_user,
    save_db=save_db,
    get_all_users=get_all_users
  )


# --- ТОЧКА ВХОДА В ПРОГРАММУ ---
# Этот блок выполняется, когда скрипт запускается напрямую
if __name__ == "__main__":
  try:
    asyncio.run(main()) # Запускаем асинхронную функцию main()
  except (KeyboardInterrupt, SystemExit):
    logger.info("🛑 Бот остановлен вручную.")
  except Exception as e:
    logger.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)