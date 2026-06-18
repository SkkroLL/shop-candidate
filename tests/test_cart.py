import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Module1_Catalog.catalog import Product
from src.Module2_Cart.cart import Cart, CartItem

class TestCart(unittest.TestCase):
    def setUp(self):
        self.product1 = Product("pr_001", "Товар 1", 100, 10, "Описание", "cat_01")
        self.product2 = Product("pr_002", "Товар 2", 200, 20, "Описание", "cat_01")
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.cart = Cart(self.temp_file.name)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_add_product(self):
        self.cart.add_product(self.product1, 2)
        items = self.cart.get_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].product.id, "pr_001")
        self.assertEqual(items[0].quantity, 2)

    def test_remove_product(self):
        self.cart.add_product(self.product1, 1)
        self.cart.add_product(self.product2, 1)
        self.cart.remove_product("pr_001")
        items = self.cart.get_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].product.id, "pr_002")

    def test_change_quantity(self):
        self.cart.add_product(self.product1, 1)
        self.cart.change_quantity("pr_001", 5)
        items = self.cart.get_items()
        self.assertEqual(items[0].quantity, 5)
        self.cart.change_quantity("pr_001", 0)
        items = self.cart.get_items()
        self.assertEqual(len(items), 0)

    def test_total(self):
        self.cart.add_product(self.product1, 2)
        self.cart.add_product(self.product2, 1)
        self.assertEqual(self.cart.get_total(), 400)

if __name__ == '__main__':
    unittest.main()