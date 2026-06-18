import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Module1_Catalog.catalog import Catalog
from Module3_Order.order import get_all_orders, update_order_status
from utils import get_logger

logger = get_logger("admin")

class AdminManager:
    """Менеджер административных функций."""
    def __init__(self, catalog):
        self.catalog = catalog

    def get_orders(self):
        """Вернуть список всех заказов."""
        return get_all_orders()

    def change_order_status(self, order_id, new_status):
        """Изменить статус заказа."""
        return update_order_status(order_id, new_status)

    def add_product(self, product_data):
        """Добавить товар через каталог."""
        # product_data должен содержать id, name, price, stock, description, category_id
        from Module1_Catalog.catalog import Product
        product = Product(
            id=product_data['id'],
            name=product_data['name'],
            price=product_data['price'],
            stock=product_data['stock'],
            description=product_data.get('description', ''),
            category_id=product_data['category_id']
        )
        self.catalog.add_product(product)
        logger.info(f"Админ добавил товар {product.name}")

    def edit_product(self, product_id, new_data):
        """Редактировать товар."""
        return self.catalog.update_product(product_id, new_data)

    def delete_product(self, product_id):
        """Удалить товар."""
        return self.catalog.delete_product(product_id)