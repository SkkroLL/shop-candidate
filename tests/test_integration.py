import unittest
import os
import sys
import tempfile
import json
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Module1_Catalog.catalog import Catalog
from src.Module2_Cart.cart import Cart
from src.Module3_Order.order import Order, init_db, get_all_orders
from src.Module4_Admin.admin import AdminManager

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.test_data = {
            "storeName": "TestStore",
            "categories": [
                {
                    "id": "cat_01",
                    "name": "Тестовая категория",
                    "products": [
                        {"id": "pr_001", "name": "Товар 1", "price": 100, "stock": 10, "description": "Описание 1"}
                    ]
                }
            ]
        }
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
        json.dump(self.test_data, self.temp_file, ensure_ascii=False, indent=2)
        self.temp_file.close()
        self.catalog = Catalog(self.temp_file.name)

        self.cart_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.cart_file.close()
        self.cart = Cart(self.cart_file.name)
        self.cart.restore_from_catalog(self.catalog)

        import src.Module3_Order.order as order_module
        self.db_path = "test_integration_orders.db"
        order_module.DB_PATH = self.db_path
        init_db()

        self.admin = AdminManager(self.catalog)

    def tearDown(self):
        os.unlink(self.temp_file.name)
        os.unlink(self.cart_file.name)
        os.unlink(self.db_path)

    def test_integration_catalog_to_cart(self):
        product = self.catalog.get_product_by_id("pr_001")
        self.cart.add_product(product, 1)
        items = self.cart.get_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].product.id, "pr_001")
        self.assertEqual(items[0].product.name, "Товар 1")
        self.assertEqual(items[0].quantity, 1)

    def test_integration_cart_to_order(self):
        product = self.catalog.get_product_by_id("pr_001")
        self.cart.add_product(product, 2)
        total = self.cart.get_total()
        customer_data = {
            'last_name': 'Иванов',
            'first_name': 'Пётр',
            'address': 'ул. Ленина, д.1',
            'phone': '+79111234567',
            'email': 'ivanov@mail.ru'
        }
        order = Order(customer_data, self.cart.get_items(), total)
        order.save_to_db()
        orders = get_all_orders()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['total'], 200)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT product_name, quantity FROM order_items WHERE order_id = ?", (order.id,))
        items = cursor.fetchall()
        conn.close()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][0], "Товар 1")
        self.assertEqual(items[0][1], 2)

    def test_integration_admin_update_catalog(self):
        new_product = {
            'id': 'pr_002',
            'name': 'Новый товар',
            'price': 150,
            'stock': 5,
            'description': 'Новое описание',
            'category_id': 'cat_01'
        }
        self.admin.add_product(new_product)
        product = self.catalog.get_product_by_id('pr_002')
        self.assertIsNotNone(product)
        self.catalog.load_data()
        product = self.catalog.get_product_by_id('pr_002')
        self.assertIsNotNone(product)

if __name__ == '__main__':
    unittest.main()