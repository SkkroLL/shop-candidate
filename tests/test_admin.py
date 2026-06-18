import unittest
import os
import sys
import tempfile
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Module1_Catalog.catalog import Catalog
from src.Module4_Admin.admin import AdminManager

class TestAdmin(unittest.TestCase):
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
        self.admin = AdminManager(self.catalog)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_add_product(self):
        product_data = {
            'id': 'pr_002',
            'name': 'Новый товар',
            'price': 150,
            'stock': 5,
            'description': 'Новое описание',
            'category_id': 'cat_01'
        }
        self.admin.add_product(product_data)
        product = self.catalog.get_product_by_id('pr_002')
        self.assertIsNotNone(product)
        self.assertEqual(product.name, 'Новый товар')

    def test_delete_product(self):
        result = self.admin.delete_product('pr_001')
        self.assertTrue(result)
        product = self.catalog.get_product_by_id('pr_001')
        self.assertIsNone(product)

    def test_edit_product(self):
        new_data = {'name': 'Изменённое название', 'price': 999}
        result = self.admin.edit_product('pr_001', new_data)
        self.assertTrue(result)
        product = self.catalog.get_product_by_id('pr_001')
        self.assertEqual(product.name, 'Изменённое название')
        self.assertEqual(product.price, 999)

if __name__ == '__main__':
    unittest.main()