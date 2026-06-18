import unittest
import os
import sys
import json
import tempfile

# Добавляем корневую папку проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Module1_Catalog.catalog import Catalog, Product, Category

class TestCatalog(unittest.TestCase):
    def setUp(self):
        self.test_data = {
            "storeName": "TestStore",
            "categories": [
                {
                    "id": "cat_01",
                    "name": "Тестовая категория",
                    "products": [
                        {"id": "pr_001", "name": "Товар 1", "price": 100, "stock": 10, "description": "Описание 1"},
                        {"id": "pr_002", "name": "Товар 2", "price": 200, "stock": 20, "description": "Описание 2"}
                    ]
                }
            ]
        }
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
        json.dump(self.test_data, self.temp_file, ensure_ascii=False, indent=2)
        self.temp_file.close()
        self.catalog = Catalog(self.temp_file.name)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_load_data(self):
        self.assertEqual(len(self.catalog.products), 2)
        self.assertEqual(len(self.catalog.categories), 1)
        self.assertEqual(self.catalog.products[0].name, "Товар 1")

    def test_search(self):
        results = self.catalog.search("Товар 1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "pr_001")

    def test_filter_by_category(self):
        results = self.catalog.filter_by_category("cat_01")
        self.assertEqual(len(results), 2)
        results = self.catalog.filter_by_category("non_existent")
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()