from django.contrib.auth.models import User
from django.db import models


# Товар (комплектующее)
class Product(models.Model):
    CATEGORIES = [
        ("cpu", "Процессоры"),
        ("mb", "Материнские платы"),
        ("ram", "Оперативная память"),
        ("gpu", "Видеокарты"),
        ("ssd", "Накопители"),
        ("cooler", "Охлаждение"),
        ("psu", "Блоки питания"),
        ("case", "Корпуса"),
    ]

    name = models.CharField("Название", max_length=200)
    category = models.CharField("Категория", max_length=20, choices=CATEGORIES)
    brand = models.CharField("Производитель", max_length=60, blank=True)
    price = models.PositiveIntegerField("Цена, ₽")
    stock = models.PositiveIntegerField("Остаток, шт.", default=0)
    description = models.TextField("Описание", blank=True)

    # характеристики для проверки совместимости в конфигураторе
    socket = models.CharField("Сокет (процессор и плата)", max_length=20, blank=True)
    ram_type = models.CharField("Тип памяти (плата и ОЗУ)", max_length=10, blank=True)
    power = models.PositiveIntegerField("Мощность, Вт (потребление или мощность БП)", default=0)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["category", "price"]

    def __str__(self):
        return self.name


# Заказ покупателя
class Order(models.Model):
    STATUSES = [
        ("new", "Новый"),
        ("work", "В работе"),
        ("sent", "Отправлен"),
        ("done", "Выполнен"),
        ("cancel", "Отменён"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Покупатель")
    name = models.CharField("Получатель", max_length=120)
    phone = models.CharField("Телефон", max_length=20)
    address = models.CharField("Адрес доставки", max_length=300)
    comment = models.TextField("Комментарий", blank=True)
    status = models.CharField("Статус", max_length=10, choices=STATUSES, default="new")
    total = models.PositiveIntegerField("Сумма, ₽", default=0)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __str__(self):
        return "Заказ №" + str(self.id)


# Строка заказа: какой товар и сколько штук
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    name = models.CharField("Товар", max_length=200)
    price = models.PositiveIntegerField("Цена, ₽")
    qty = models.PositiveIntegerField("Количество")

    def sum(self):
        return self.price * self.qty
