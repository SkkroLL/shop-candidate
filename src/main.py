import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QComboBox, QLabel, QSpinBox, QMessageBox, QGroupBox,
    QFormLayout, QTextEdit, QHeaderView, QDoubleSpinBox
)
from PyQt5.QtCore import Qt

# Добавляем пути для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import get_logger
from Module1_Catalog.catalog import Catalog
from Module2_Cart.cart import Cart
from Module3_Order.order import validate_customer_data, Order
from Module4_Admin.admin import AdminManager

logger = get_logger("main")

# Путь к JSON-файлу с товарами (относительно корня src)
PRODUCTS_JSON = os.path.join(os.path.dirname(__file__), "data", "products.json")
CART_JSON = os.path.join(os.path.dirname(__file__), "cart.json")  # для хранения корзины

class CatalogTab(QWidget):
    """Вкладка каталога."""
    def __init__(self, catalog, cart):
        super().__init__()
        self.catalog = catalog
        self.cart = cart
        self.initUI()
        self.refresh_table()

    def initUI(self):
        layout = QVBoxLayout()

        # Верхняя панель: поиск, фильтр по категории, фильтр по цене
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по названию...")
        self.search_btn = QPushButton("Найти")
        self.search_btn.clicked.connect(self.refresh_table)

        self.category_filter = QComboBox()
        self.category_filter.addItem("Все категории", None)
        for cat in self.catalog.categories:
            self.category_filter.addItem(cat.name, cat.id)
        self.category_filter.currentIndexChanged.connect(self.refresh_table)

        self.price_min = QDoubleSpinBox()
        self.price_min.setRange(0, 100000)
        self.price_min.setPrefix("от ")
        self.price_max = QDoubleSpinBox()
        self.price_max.setRange(0, 100000)
        self.price_max.setPrefix("до ")

        filter_btn = QPushButton("Применить фильтр цен")
        filter_btn.clicked.connect(self.refresh_table)

        top_layout.addWidget(QLabel("Поиск:"))
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.search_btn)
        top_layout.addWidget(QLabel("Категория:"))
        top_layout.addWidget(self.category_filter)
        top_layout.addWidget(QLabel("Цена:"))
        top_layout.addWidget(self.price_min)
        top_layout.addWidget(self.price_max)
        top_layout.addWidget(filter_btn)
        top_layout.addStretch()

        layout.addLayout(top_layout)

        # Таблица товаров
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Цена", "Остаток", "Категория"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        # Кнопка добавления в корзину
        add_btn = QPushButton("Добавить выбранный товар в корзину")
        add_btn.clicked.connect(self.add_to_cart)
        layout.addWidget(add_btn)

        self.setLayout(layout)

    def refresh_table(self):
        """Обновить таблицу с учётом фильтров."""
        # Получаем все товары
        products = self.catalog.get_all_products()
        # Поиск
        query = self.search_input.text()
        if query:
            products = self.catalog.search(query)
        # Фильтр по категории
        cat_id = self.category_filter.currentData()
        if cat_id:
            products = [p for p in products if p.category_id == cat_id]
        # Фильтр по цене
        min_price = self.price_min.value()
        max_price = self.price_max.value()
        if min_price > 0 or max_price > 0:
            if min_price > 0 and max_price > 0 and min_price > max_price:
                QMessageBox.warning(self, "Ошибка", "Минимальная цена не может быть больше максимальной.")
                return
            products = self.catalog.filter_by_price(min_price if min_price > 0 else None,
                                                     max_price if max_price > 0 else None)

        self.table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.table.setItem(i, 0, QTableWidgetItem(p.id))
            self.table.setItem(i, 1, QTableWidgetItem(p.name))
            self.table.setItem(i, 2, QTableWidgetItem(f"{p.price:.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(str(p.stock)))
            # Название категории
            cat_name = ""
            for cat in self.catalog.categories:
                if cat.id == p.category_id:
                    cat_name = cat.name
                    break
            self.table.setItem(i, 4, QTableWidgetItem(cat_name))

    def add_to_cart(self):
        """Добавить выбранный товар в корзину."""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Внимание", "Выберите товар для добавления.")
            return
        product_id = self.table.item(selected, 0).text()
        product = self.catalog.get_product_by_id(product_id)
        if product:
            self.cart.add_product(product, 1)
            QMessageBox.information(self, "Успех", f"Товар '{product.name}' добавлен в корзину.")
        else:
            QMessageBox.critical(self, "Ошибка", "Товар не найден.")

class CartTab(QWidget):
    """Вкладка корзины."""
    def __init__(self, cart, catalog):
        super().__init__()
        self.cart = cart
        self.catalog = catalog
        self.initUI()
        self.refresh_table()

    def initUI(self):
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Название", "Цена", "Количество", "Сумма"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Информация об общей сумме
        self.total_label = QLabel("Общая сумма: 0.00 руб.")
        layout.addWidget(self.total_label)

        # Панель управления
        btn_layout = QHBoxLayout()
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999)
        self.quantity_spin.setValue(1)
        change_qty_btn = QPushButton("Изменить количество")
        change_qty_btn.clicked.connect(self.change_quantity)
        remove_btn = QPushButton("Удалить выбранный товар")
        remove_btn.clicked.connect(self.remove_item)
        clear_btn = QPushButton("Очистить корзину")
        clear_btn.clicked.connect(self.clear_cart)

        btn_layout.addWidget(QLabel("Новое количество:"))
        btn_layout.addWidget(self.quantity_spin)
        btn_layout.addWidget(change_qty_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def refresh_table(self):
        """Обновить таблицу корзины."""
        items = self.cart.get_items()
        self.table.setRowCount(len(items))
        total = 0
        for i, item in enumerate(items):
            self.table.setItem(i, 0, QTableWidgetItem(item.product.name))
            self.table.setItem(i, 1, QTableWidgetItem(f"{item.product.price:.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(str(item.quantity)))
            subtotal = item.total_price()
            total += subtotal
            self.table.setItem(i, 3, QTableWidgetItem(f"{subtotal:.2f}"))
        self.total_label.setText(f"Общая сумма: {total:.2f} руб.")

    def change_quantity(self):
        """Изменить количество выбранного товара."""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Внимание", "Выберите товар для изменения.")
            return
        item = self.cart.get_items()[selected]
        new_qty = self.quantity_spin.value()
        self.cart.change_quantity(item.product.id, new_qty)
        self.refresh_table()

    def remove_item(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Внимание", "Выберите товар для удаления.")
            return
        item = self.cart.get_items()[selected]
        self.cart.remove_product(item.product.id)
        self.refresh_table()

    def clear_cart(self):
        if self.cart.get_items():
            reply = QMessageBox.question(self, "Подтверждение", "Очистить корзину?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.cart.clear()
                self.refresh_table()

class OrderTab(QWidget):
    """Вкладка оформления заказа."""
    def __init__(self, cart, catalog):
        super().__init__()
        self.cart = cart
        self.catalog = catalog
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        group = QGroupBox("Данные покупателя")
        form = QFormLayout()
        self.last_name_edit = QLineEdit()
        self.first_name_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        form.addRow("Фамилия:", self.last_name_edit)
        form.addRow("Имя:", self.first_name_edit)
        form.addRow("Адрес:", self.address_edit)
        form.addRow("Телефон:", self.phone_edit)
        form.addRow("Email:", self.email_edit)
        group.setLayout(form)
        layout.addWidget(group)

        # Кнопка оформления
        order_btn = QPushButton("Оформить заказ")
        order_btn.clicked.connect(self.place_order)
        layout.addWidget(order_btn)

        # Текстовое поле для отображения результатов
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

        self.setLayout(layout)

    def place_order(self):
        """Обработка оформления заказа."""
        # Проверяем, не пуста ли корзина
        if not self.cart.get_items():
            QMessageBox.warning(self, "Ошибка", "Корзина пуста. Добавьте товары.")
            return

        # Собираем данные
        data = {
            'last_name': self.last_name_edit.text(),
            'first_name': self.first_name_edit.text(),
            'address': self.address_edit.text(),
            'phone': self.phone_edit.text(),
            'email': self.email_edit.text()
        }
        valid, error = validate_customer_data(data)
        if not valid:
            QMessageBox.critical(self, "Ошибка валидации", error)
            return

        # Создаём заказ
        total = self.cart.get_total()
        order = Order(data, self.cart.get_items(), total)
        if order.save_to_db():
            # Очищаем корзину
            self.cart.clear()
            self.result_text.setText(f"Заказ успешно оформлен!\nНомер заказа: {order.id}\n"
                                     f"Общая сумма: {total:.2f} руб.\nСпасибо за покупку!")
            # Очищаем поля ввода
            for edit in [self.last_name_edit, self.first_name_edit, self.address_edit,
                         self.phone_edit, self.email_edit]:
                edit.clear()
            QMessageBox.information(self, "Успех", f"Заказ {order.id} оформлен!")
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить заказ. Проверьте логи.")

class AdminTab(QWidget):
    """Вкладка администратора."""
    def __init__(self, admin_manager, catalog):
        super().__init__()
        self.admin = admin_manager
        self.catalog = catalog
        self.initUI()
        self.refresh_orders()

    def initUI(self):
        layout = QVBoxLayout()

        # Подвкладка: заказы
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(6)
        self.order_table.setHorizontalHeaderLabels(["ID", "Покупатель", "Сумма", "Статус", "Дата", "Действие"])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("Список заказов:"))
        layout.addWidget(self.order_table)

        # Выбор статуса для изменения
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Изменить статус заказа ID:"))
        self.order_id_edit = QLineEdit()
        self.order_id_edit.setPlaceholderText("Введите ID заказа")
        status_layout.addWidget(self.order_id_edit)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["новый", "в обработке", "доставлен", "отменён"])
        status_layout.addWidget(self.status_combo)
        change_status_btn = QPushButton("Изменить статус")
        change_status_btn.clicked.connect(self.change_status)
        status_layout.addWidget(change_status_btn)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Кнопка обновления списка заказов
        refresh_btn = QPushButton("Обновить список заказов")
        refresh_btn.clicked.connect(self.refresh_orders)
        layout.addWidget(refresh_btn)

        # Разделитель
        layout.addWidget(QLabel("--- Управление товарами ---"))

        # Форма добавления/редактирования товара
        form_group = QGroupBox("Добавить/редактировать товар")
        form = QFormLayout()
        self.product_id_edit = QLineEdit()
        self.product_id_edit.setPlaceholderText("Уникальный ID (например, pr_999)")
        self.product_name_edit = QLineEdit()
        self.product_name_edit.setPlaceholderText("Название")
        self.product_price_edit = QDoubleSpinBox()
        self.product_price_edit.setRange(0, 100000)
        self.product_price_edit.setPrefix("₽ ")
        self.product_stock_edit = QSpinBox()
        self.product_stock_edit.setRange(0, 99999)
        self.product_desc_edit = QLineEdit()
        self.product_cat_combo = QComboBox()
        # Заполняем категориями
        for cat in self.catalog.categories:
            self.product_cat_combo.addItem(cat.name, cat.id)

        form.addRow("ID:", self.product_id_edit)
        form.addRow("Название:", self.product_name_edit)
        form.addRow("Цена:", self.product_price_edit)
        form.addRow("Остаток:", self.product_stock_edit)
        form.addRow("Описание:", self.product_desc_edit)
        form.addRow("Категория:", self.product_cat_combo)
        form_group.setLayout(form)
        layout.addWidget(form_group)

        # Кнопки управления товарами
        btn_layout = QHBoxLayout()
        add_product_btn = QPushButton("Добавить товар")
        add_product_btn.clicked.connect(self.add_product)
        delete_product_btn = QPushButton("Удалить товар по ID")
        delete_product_btn.clicked.connect(self.delete_product)
        btn_layout.addWidget(add_product_btn)
        btn_layout.addWidget(delete_product_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def refresh_orders(self):
        """Обновить таблицу заказов."""
        orders = self.admin.get_orders()
        self.order_table.setRowCount(len(orders))
        for i, order in enumerate(orders):
            self.order_table.setItem(i, 0, QTableWidgetItem(order['id']))
            self.order_table.setItem(i, 1, QTableWidgetItem(f"{order['last_name']} {order['first_name']}"))
            self.order_table.setItem(i, 2, QTableWidgetItem(f"{order['total']:.2f}"))
            self.order_table.setItem(i, 3, QTableWidgetItem(order['status']))
            self.order_table.setItem(i, 4, QTableWidgetItem(order['created_at']))
            # Кнопка "Изменить статус" (можно добавить, но мы используем отдельные поля)
            # Для простоты оставляем пустым

    def change_status(self):
        order_id = self.order_id_edit.text().strip()
        if not order_id:
            QMessageBox.warning(self, "Ошибка", "Введите ID заказа.")
            return
        new_status = self.status_combo.currentText()
        if self.admin.change_order_status(order_id, new_status):
            QMessageBox.information(self, "Успех", f"Статус заказа {order_id} изменён на {new_status}.")
            self.refresh_orders()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось изменить статус. Проверьте ID и логи.")

    def add_product(self):
        """Добавление нового товара."""
        pid = self.product_id_edit.text().strip()
        name = self.product_name_edit.text().strip()
        price = self.product_price_edit.value()
        stock = self.product_stock_edit.value()
        desc = self.product_desc_edit.text().strip()
        cat_id = self.product_cat_combo.currentData()
        if not pid or not name:
            QMessageBox.warning(self, "Ошибка", "ID и название товара обязательны.")
            return
        # Проверка на уникальность ID
        if self.catalog.get_product_by_id(pid):
            QMessageBox.warning(self, "Ошибка", f"Товар с ID {pid} уже существует.")
            return
        product_data = {
            'id': pid,
            'name': name,
            'price': price,
            'stock': stock,
            'description': desc,
            'category_id': cat_id
        }
        self.admin.add_product(product_data)
        QMessageBox.information(self, "Успех", f"Товар {name} добавлен.")
        # Обновить каталог (он уже обновлён внутри)
        # Очистить поля
        self.product_id_edit.clear()
        self.product_name_edit.clear()
        self.product_price_edit.setValue(0)
        self.product_stock_edit.setValue(0)
        self.product_desc_edit.clear()

    def delete_product(self):
        pid = self.product_id_edit.text().strip()
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Введите ID товара для удаления.")
            return
        if self.admin.delete_product(pid):
            QMessageBox.information(self, "Успех", f"Товар {pid} удалён.")
            self.product_id_edit.clear()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось удалить товар. Проверьте ID.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("КанцТовары - Интернет-магазин")
        self.setGeometry(100, 100, 1000, 700)

        # Инициализация модулей
        self.catalog = Catalog(PRODUCTS_JSON)
        self.cart = Cart(CART_JSON)
        # Восстанавливаем корзину из файла
        self.cart.restore_from_catalog(self.catalog)

        # Админ-менеджер
        self.admin = AdminManager(self.catalog)

        # Создаём вкладки
        tabs = QTabWidget()
        self.catalog_tab = CatalogTab(self.catalog, self.cart)
        self.cart_tab = CartTab(self.cart, self.catalog)
        self.order_tab = OrderTab(self.cart, self.catalog)
        self.admin_tab = AdminTab(self.admin, self.catalog)

        tabs.addTab(self.catalog_tab, "Каталог")
        tabs.addTab(self.cart_tab, "Корзина")
        tabs.addTab(self.order_tab, "Оформление заказа")
        tabs.addTab(self.admin_tab, "Администрирование")

        self.setCentralWidget(tabs)

        # Обновляем корзину при переключении вкладок
        tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        # Если переключились на вкладку корзины или заказа, обновляем их
        if index == 1:  # Корзина
            self.cart_tab.refresh_table()
        elif index == 2:  # Заказ
            # Можно обновить что-то
            pass
        elif index == 3:  # Админка
            self.admin_tab.refresh_orders()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())