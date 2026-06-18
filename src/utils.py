import json
import logging
import os
from datetime import datetime

# Настройка логирования
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()  # вывод в консоль
    ]
)

def get_logger(name):
    """Получить логгер с именем модуля."""
    return logging.getLogger(name)

def load_json(filepath):
    """Загрузить JSON из файла, вернуть словарь. При ошибке вернуть None и записать лог."""
    logger = get_logger("utils")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Файл не найден: {filepath}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON в {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Неизвестная ошибка при загрузке {filepath}: {e}")
        return None

def save_json(filepath, data):
    """Сохранить данные в JSON-файл. Вернуть True при успехе."""
    logger = get_logger("utils")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения JSON в {filepath}: {e}")
        return False

def generate_order_id():
    """Сгенерировать уникальный номер заказа на основе времени и случайного числа."""
    from random import randint
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"ORD-{now}-{randint(100, 999)}"