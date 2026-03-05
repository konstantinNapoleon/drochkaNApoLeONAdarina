import json
import os
from aiogram import Router, types, F

router = Router()

# Путь к файлу, где будут храниться данные о кодах
BONUS_DATA_FILE = "bonus_data.json"

def save_bonus_data():
  """Сохраняет текущее состояние BONUS_CODES в файл"""
  with open(BONUS_DATA_FILE, "w", encoding="utf-8") as f:
    # Сериализуем данные (превращаем datetime в строку для JSON)
    data_to_save = {}
    for code, info in BONUS_CODES.items():
      data_to_save[code] = info.copy()
      data_to_save[code]['expires'] = info['expires'].strftime("%Y-%m-%d %H:%M:%S")
    json.dump(data_to_save, f, ensure_ascii=False, indent=4)

def load_bonus_data():
  """Загружает состояние BONUS_CODES из файла при запуске"""
  global BONUS_CODES
  if os.path.exists(BONUS_DATA_FILE):
    with open(BONUS_DATA_FILE, "r", encoding="utf-8") as f:
      loaded_data = json.load(f)
      for code, info in loaded_data.items():
        if code in BONUS_CODES:
          BONUS_CODES[code]['used_count'] = info['used_count']
          BONUS_CODES[code]['claimed_by'] = info['claimed_by']

# Вызываем загрузку сразу при старте скрипта
load_bonus_data()