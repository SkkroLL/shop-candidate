import os
import sys
# Добавляем путь к корню src для импорта utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_json, save_json, get_logger

logger = get_logger("catalog")

class Product:
    """Модель товара."""
    def __init__(self, id, name, price, stock, description, category_id):
        self.id = id
        self.name = name
        self.price = price
        self.stock = stock
        self.description = description
        self.category_id = category_id

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "description": self.description,
            "category_id": self.category_id
        }

class Category:
    """Модель категории."""
    def __init__(self, id, name, products=None):
        self.id = id
        self.name = name
        self.products = products if products is not None else []

class Catalog:
    """Управление каталогом товаров."""
    def __init__(self, json_path):
        self.json_path = json_path
        self.categories = []  # список Category
        self.products = []    # список Product (плоский для удобства)
        self.load_data()

    def load_data(self):
        """Загрузить данные из JSON-файла."""
        data = load_json(self.json_path)
        if data is None:
            logger.error("Не удалось загрузить каталог. Будет создан пустой.")
            self.categories = []
            self.products = []
            return

        self.categories = []
        self.products = []
        for cat_data in data.get("categories", []):
            cat = Category(cat_data["id"], cat_data["name"])
            for prod_data in cat_data.get("products", []):
                product = Product(
                    id=prod_data["id"],
                    name=prod_data["name"],
                    price=prod_data["price"],
                    stock=prod_data["stock"],
                    description=prod_data.get("description", ""),
                    category_id=cat.id
                )
                cat.products.append(product)
                self.products.append(product)
            self.categories.append(cat)
        logger.info(f"Загружено {len(self.products)} товаров в {len(self.categories)} категориях.")

    def get_all_products(self):
        """Вернуть список всех товаров."""
        return self.products

    def search(self, query):
        """Поиск по названию (регистронезависимый)."""
        query = query.lower().strip()
        if not query:
            return self.products
        return [p for p in self.products if query in p.name.lower()]

    def filter_by_category(self, category_id):
        """Фильтр по категории."""
        if not category_id:
            return self.products
        return [p for p in self.products if p.category_id == category_id]

    def filter_by_price(self, min_price=None, max_price=None):
        """Фильтр по диапазону цен."""
        result = self.products
        if min_price is not None:
            result = [p for p in result if p.price >= min_price]
        if max_price is not None:
            result = [p for p in result if p.price <= max_price]
        return result

    def get_product_by_id(self, product_id):
        """Найти товар по ID."""
        for p in self.products:
            if p.id == product_id:
                return p
        return None

    def add_product(self, product):
        """Добавить новый товар (в память и в JSON)."""
        self.products.append(product)
        # Добавляем в соответствующую категорию
        for cat in self.categories:
            if cat.id == product.category_id:
                cat.products.append(product)
                break
        else:
            # Если категория не найдена, создаём новую (можно доработать)
            logger.warning(f"Категория {product.category_id} не найдена, создаём.")
            new_cat = Category(product.category_id, product.category_id)
            new_cat.products.append(product)
            self.categories.append(new_cat)
        self._save_to_json()
        logger.info(f"Добавлен товар {product.name} (ID: {product.id})")

    def update_product(self, product_id, new_data):
        """Обновить данные товара."""
        product = self.get_product_by_id(product_id)
        if not product:
            logger.error(f"Товар с ID {product_id} не найден.")
            return False
        # Обновляем поля
        for key, value in new_data.items():
            if hasattr(product, key):
                setattr(product, key, value)
        self._save_to_json()
        logger.info(f"Обновлён товар {product_id}")
        return True

    def delete_product(self, product_id):
        """Удалить товар по ID."""
        product = self.get_product_by_id(product_id)
        if not product:
            logger.error(f"Товар с ID {product_id} не найден.")
            return False
        # Удалить из плоского списка
        self.products = [p for p in self.products if p.id != product_id]
        # Удалить из категорий
        for cat in self.categories:
            cat.products = [p for p in cat.products if p.id != product_id]
        self._save_to_json()
        logger.info(f"Удалён товар {product_id}")
        return True

    def _save_to_json(self):
        """Сохранить текущее состояние каталога в JSON."""
        data = {
            "storeName": "КанцТовары",  # можно сделать параметром
            "categories": []
        }
        for cat in self.categories:
            cat_dict = {
                "id": cat.id,
                "name": cat.name,
                "products": [p.to_dict() for p in cat.products]
            }
            data["categories"].append(cat_dict)
        if not save_json(self.json_path, data):
            logger.error("Не удалось сохранить каталог.")
        else:
            logger.info("Каталог сохранён в JSON.")