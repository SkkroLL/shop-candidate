import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_logger, save_json, load_json

logger = get_logger("cart")

class CartItem:
    """Элемент корзины: товар и количество."""
    def __init__(self, product, quantity=1):
        self.product = product
        self.quantity = quantity

    def total_price(self):
        return self.product.price * self.quantity

class Cart:
    """Корзина покупок."""
    def __init__(self, storage_file="cart.json"):
        self.storage_file = storage_file
        self.items = []  # список CartItem
        self.load()

    def add_product(self, product, quantity=1):
        """Добавить товар, если уже есть - увеличить количество."""
        for item in self.items:
            if item.product.id == product.id:
                item.quantity += quantity
                self.save()
                logger.info(f"Увеличено количество товара {product.name} до {item.quantity}")
                return
        self.items.append(CartItem(product, quantity))
        self.save()
        logger.info(f"Добавлен товар {product.name} в корзину (кол-во: {quantity})")

    def remove_product(self, product_id):
        """Удалить товар полностью."""
        self.items = [item for item in self.items if item.product.id != product_id]
        self.save()
        logger.info(f"Удалён товар с ID {product_id} из корзины")

    def change_quantity(self, product_id, new_quantity):
        """Изменить количество товара. Если <=0, удалить."""
        for item in self.items:
            if item.product.id == product_id:
                if new_quantity <= 0:
                    self.remove_product(product_id)
                else:
                    item.quantity = new_quantity
                    self.save()
                    logger.info(f"Изменено количество товара {item.product.name} на {new_quantity}")
                return

    def get_total(self):
        """Общая сумма корзины."""
        return sum(item.total_price() for item in self.items)

    def clear(self):
        """Очистить корзину."""
        self.items.clear()
        self.save()
        logger.info("Корзина очищена")

    def get_items(self):
        """Вернуть список элементов."""
        return self.items

    def save(self):
        """Сохранить корзину в JSON-файл."""
        data = []
        for item in self.items:
            data.append({
                "product_id": item.product.id,
                "quantity": item.quantity
            })
        if not save_json(self.storage_file, data):
            logger.error("Не удалось сохранить корзину")
        else:
            logger.info("Корзина сохранена")

    def load(self):
        """Загрузить корзину из JSON-файла (требует внешнего каталога для восстановления товаров)."""
        # Восстановление корзины требует доступа к каталогу, поэтому этот метод будет вызываться
        # из main после инициализации каталога. Здесь мы просто загружаем список ID и количеств,
        # а наполнение товарами будет выполнено отдельным методом.
        data = load_json(self.storage_file)
        if data is not None:
            # Сохраним сырые данные для последующего восстановления
            self._raw_data = data
        else:
            self._raw_data = []

    def restore_from_catalog(self, catalog):
        """Восстановить объекты товаров из каталога."""
        self.items = []
        for entry in self._raw_data:
            product = catalog.get_product_by_id(entry["product_id"])
            if product:
                self.items.append(CartItem(product, entry["quantity"]))
            else:
                logger.warning(f"Товар {entry['product_id']} не найден в каталоге, пропущен.")
        self._raw_data = []  # очищаем после восстановления
        logger.info(f"Корзина восстановлена: {len(self.items)} позиций")