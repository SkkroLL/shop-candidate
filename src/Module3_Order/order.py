import os
import sys
import sqlite3
import re
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_logger, generate_order_id

logger = get_logger("order")

DB_PATH = "orders.db"  # будет создан в корне проекта

def init_db():
    """Создать таблицы для заказов, если их нет."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            last_name TEXT,
            first_name TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            total REAL,
            status TEXT DEFAULT 'новый',
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            order_id TEXT,
            product_id TEXT,
            product_name TEXT,
            price REAL,
            quantity INTEGER,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("База данных заказов инициализирована")

def validate_customer_data(data):
    """
    Проверка данных покупателя.
    data: dict с полями last_name, first_name, address, phone, email.
    Возвращает (is_valid, error_message)
    """
    required_fields = ['last_name', 'first_name', 'address', 'phone', 'email']
    for field in required_fields:
        if not data.get(field, '').strip():
            return False, f"Поле '{field}' обязательно для заполнения."

    # Проверка телефона (простейшая: только цифры, +, пробелы, скобки, дефисы)
    phone = data['phone'].strip()
    if not re.match(r'^[\+\d\s\-\(\)]{7,15}$', phone):
        return False, "Неверный формат телефона. Используйте цифры и знак +."

    # Проверка email
    email = data['email'].strip()
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False, "Неверный формат email."

    return True, ""

class Order:
    """Модель заказа."""
    def __init__(self, customer_data, cart_items, total):
        self.id = generate_order_id()
        self.last_name = customer_data['last_name'].strip()
        self.first_name = customer_data['first_name'].strip()
        self.address = customer_data['address'].strip()
        self.phone = customer_data['phone'].strip()
        self.email = customer_data['email'].strip()
        self.total = total
        self.status = "новый"
        self.created_at = datetime.now().isoformat()
        self.items = []  # список кортежей (product_id, product_name, price, quantity)
        for item in cart_items:
            self.items.append((item.product.id, item.product.name, item.product.price, item.quantity))

    def save_to_db(self):
        """Сохранить заказ в базу данных."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO orders (id, last_name, first_name, address, phone, email, total, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.id, self.last_name, self.first_name, self.address, self.phone,
                  self.email, self.total, self.status, self.created_at))
            for product_id, product_name, price, quantity in self.items:
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.id, product_id, product_name, price, quantity))
            conn.commit()
            logger.info(f"Заказ {self.id} сохранён в БД")
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка сохранения заказа: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def get_all_orders():
    """Получить список всех заказов из БД."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, last_name, first_name, address, phone, email, total, status, created_at
        FROM orders ORDER BY created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    orders = []
    for row in rows:
        orders.append({
            'id': row[0],
            'last_name': row[1],
            'first_name': row[2],
            'address': row[3],
            'phone': row[4],
            'email': row[5],
            'total': row[6],
            'status': row[7],
            'created_at': row[8]
        })
    return orders

def update_order_status(order_id, new_status):
    """Изменить статус заказа."""
    valid_statuses = ['новый', 'в обработке', 'доставлен', 'отменён']
    if new_status not in valid_statuses:
        logger.error(f"Недопустимый статус: {new_status}")
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
        conn.commit()
        logger.info(f"Статус заказа {order_id} изменён на {new_status}")
        return True
    except sqlite3.Error as e:
        logger.error(f"Ошибка обновления статуса: {e}")
        return False
    finally:
        conn.close()

# Инициализация БД при импорте
init_db()