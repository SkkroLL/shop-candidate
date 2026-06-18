import unittest
import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Module3_Order.order import validate_customer_data, init_db, get_all_orders, update_order_status, Order
from src.Module1_Catalog.catalog import Product

class TestOrder(unittest.TestCase):
    def setUp(self):
        # Переопределяем путь к БД для тестов
        import src.Module3_Order.order as order_module
        self.db_path = "test_orders.db"
        order_module.DB_PATH = self.db_path
        init_db()

    def tearDown(self):
        os.unlink(self.db_path)

    def test_validate_customer_data_valid(self):
        data = {
            'last_name': 'Иванов',
            'first_name': 'Пётр',
            'address': 'ул. Ленина, д.1',
            'phone': '+79111234567',
            'email': 'ivanov@mail.ru'
        }
        valid, error = validate_customer_data(data)
        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_validate_customer_data_empty_field(self):
        data = {
            'last_name': '',
            'first_name': 'Пётр',
            'address': 'ул. Ленина, д.1',
            'phone': '+79111234567',
            'email': 'ivanov@mail.ru'
        }
        valid, error = validate_customer_data(data)
        self.assertFalse(valid)
        self.assertIn('last_name', error)

    def test_validate_customer_data_invalid_phone(self):
        data = {
            'last_name': 'Иванов',
            'first_name': 'Пётр',
            'address': 'ул. Ленина, д.1',
            'phone': 'не телефон',
            'email': 'ivanov@mail.ru'
        }
        valid, error = validate_customer_data(data)
        self.assertFalse(valid)
        self.assertIn('телефона', error)

    def test_save_order(self):
        customer_data = {
            'last_name': 'Иванов',
            'first_name': 'Пётр',
            'address': 'ул. Ленина, д.1',
            'phone': '+79111234567',
            'email': 'ivanov@mail.ru'
        }
        product = Product("pr_001", "Товар", 100, 10, "Описание", "cat_01")
        class CartItemMock:
            def __init__(self, prod):
                self.product = prod
                self.quantity = 2
        cart_items = [CartItemMock(product)]
        order = Order(customer_data, cart_items, 200)
        result = order.save_to_db()
        self.assertTrue(result)
        orders = get_all_orders()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['id'], order.id)
        self.assertEqual(orders[0]['last_name'], 'Иванов')

if __name__ == '__main__':
    unittest.main()