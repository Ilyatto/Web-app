from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from openpyxl import Workbook

from .forms import ProductForm
from .models import Order, OrderItem, Product


# Каталог

def catalog(request):
    products = Product.objects.all()

    # фильтр по категории
    category = request.GET.get("cat", "")
    if category != "":
        products = products.filter(category=category)

    # поиск по названию
    query = request.GET.get("q", "")
    if query != "":
        products = products.filter(name__icontains=query)

    return render(request, "shop/catalog.html", {
        "products": products,
        "categories": Product.CATEGORIES,
        "category": category,
        "query": query,
    })


def product_page(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, "shop/product.html", {"product": product})


# Конфигуратор

def check_build(parts):
    # parts – словарь {категория: товар}, возвращает список ошибок совместимости
    errors = []
    cpu = parts.get("cpu")
    mb = parts.get("mb")
    ram = parts.get("ram")
    gpu = parts.get("gpu")
    psu = parts.get("psu")

    # 1. сокет процессора и материнской платы
    if cpu and mb and cpu.socket != mb.socket:
        errors.append("Процессор (сокет " + cpu.socket + ") не подходит к плате (сокет " + mb.socket + ")")

    # 2. тип памяти у платы и оперативной памяти
    if mb and ram and mb.ram_type != ram.ram_type:
        errors.append("Плата поддерживает " + mb.ram_type + ", а выбрана память " + ram.ram_type)

    # 3. хватает ли мощности блока питания (+100 Вт на остальные детали)
    if psu:
        need = 100
        if cpu:
            need = need + cpu.power
        if gpu:
            need = need + gpu.power
        if psu.power < need:
            errors.append("Блока питания " + str(psu.power) + " Вт мало, нужно хотя бы " + str(need) + " Вт")

    return errors


def builder(request):
    parts = {}  # выбранные детали {категория: товар}

    # читаем, что выбрал пользователь в каждом списке
    if request.method == "POST":
        for cat in Product.CATEGORIES:
            product_id = request.POST.get(cat[0])
            if product_id:
                parts[cat[0]] = Product.objects.get(id=int(product_id))

    # общая цена сборки
    total = 0
    for product in parts.values():
        total = total + product.price

    errors = check_build(parts)

    # кнопка «Добавить в корзину»
    if request.method == "POST" and request.POST.get("action") == "cart":
        if not request.user.is_authenticated:
            messages.error(request, "Войдите, чтобы добавить сборку в корзину")
            return redirect("login")
        if len(parts) == 0:
            messages.error(request, "Выберите хотя бы одну деталь")
        elif len(errors) > 0:
            messages.error(request, "Сначала исправьте несовместимость")
        else:
            cart = get_cart(request)
            for product in parts.values():
                key = str(product.id)
                if key in cart:
                    cart[key] = cart[key] + 1
                else:
                    cart[key] = 1
            request.session["cart"] = cart
            messages.success(request, "Сборка добавлена в корзину")
            return redirect("cart")

    # для каждой категории: название, список товаров и выбранный товар
    rows = []
    for cat in Product.CATEGORIES:
        rows.append({
            "code": cat[0],
            "title": cat[1],
            "products": Product.objects.filter(category=cat[0]),
            "selected": parts.get(cat[0]),
        })

    return render(request, "shop/builder.html", {
        "rows": rows,
        "total": total,
        "errors": errors,
        "checked": request.method == "POST" and len(parts) > 0,
    })


# Регистрация, вход, выход

def register_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Такой логин уже занят")
        elif len(password) < 6:
            messages.error(request, "Пароль должен быть не короче 6 символов")
        elif password != password2:
            messages.error(request, "Пароли не совпадают")
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect("catalog")

    return render(request, "shop/register.html")


def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Неверный логин или пароль")
        else:
            login(request, user)
            # сотрудника сразу отправляем к заказам
            if user.is_staff:
                return redirect("staff_orders")
            return redirect("catalog")

    return render(request, "shop/login.html")


def logout_page(request):
    logout(request)
    return redirect("catalog")


# Корзина
# Корзина хранится в сессии в виде словаря {id товара: количество}

def get_cart(request):
    return request.session.get("cart", {})


def get_cart_rows(cart):
    # превращаем корзину в список строк: товар, количество, сумма
    rows = []
    total = 0
    for key in cart:
        product = Product.objects.filter(id=int(key)).first()
        if product is None:
            continue  # товар удалили из каталога
        qty = cart[key]
        rows.append({"product": product, "qty": qty, "sum": product.price * qty})
        total = total + product.price * qty
    return rows, total


@login_required
def cart_add(request, id):
    cart = get_cart(request)
    key = str(id)

    if key in cart:
        cart[key] = cart[key] + 1
    else:
        cart[key] = 1

    request.session["cart"] = cart
    messages.success(request, "Товар добавлен в корзину")
    return redirect("catalog")


@login_required
def cart_remove(request, id):
    cart = get_cart(request)
    key = str(id)

    if key in cart:
        del cart[key]

    request.session["cart"] = cart
    return redirect("cart")


@login_required
def cart_page(request):
    cart = get_cart(request)

    # меняем количество товара
    if request.method == "POST":
        key = request.POST.get("product")
        qty = int(request.POST.get("qty"))
        if qty > 0:
            cart[key] = qty
        request.session["cart"] = cart
        return redirect("cart")

    rows, total = get_cart_rows(cart)
    return render(request, "shop/cart.html", {"rows": rows, "total": total})


# Оформление заказа

@login_required
def checkout(request):
    rows, total = get_cart_rows(get_cart(request))
    if len(rows) == 0:
        return redirect("cart")

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        comment = request.POST.get("comment")

        # в номере должно быть 11 цифр: 7 и ещё 10
        digits = ""
        for ch in phone:
            if ch.isdigit():
                digits = digits + ch

        if name == "" or address == "":
            messages.error(request, "Заполните имя и адрес")
        elif len(digits) != 11:
            messages.error(request, "Введите телефон полностью")
        else:
            # проверяем, хватает ли товара на складе
            for row in rows:
                product = row["product"]
                if product.stock < row["qty"]:
                    messages.error(request, "Товара «" + product.name + "» осталось только " + str(product.stock) + " шт.")
                    return redirect("cart")

            # создаём заказ
            order = Order.objects.create(user=request.user, name=name, phone=phone,
                                         address=address, comment=comment, total=total)

            # добавляем товары в заказ и списываем со склада
            for row in rows:
                product = row["product"]
                OrderItem.objects.create(order=order, product=product, name=product.name,
                                         price=product.price, qty=row["qty"])
                product.stock = product.stock - row["qty"]
                product.save()

            # очищаем корзину
            request.session["cart"] = {}
            messages.success(request, "Заказ №" + str(order.id) + " оформлен")
            return redirect("my_orders")

    return render(request, "shop/checkout.html", {"rows": rows, "total": total})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, "shop/orders.html", {"orders": orders})


# Раздел сотрудника
# В каждой функции проверяем, что пользователь сотрудник (is_staff)

@login_required
def staff_orders(request):
    if not request.user.is_staff:
        return redirect("catalog")

    orders = Order.objects.all()

    status = request.GET.get("status", "")
    if status != "":
        orders = orders.filter(status=status)

    return render(request, "staff/orders.html", {
        "orders": orders,
        "statuses": Order.STATUSES,
        "status": status,
    })


@login_required
def staff_order(request, id):
    if not request.user.is_staff:
        return redirect("catalog")

    order = get_object_or_404(Order, id=id)

    # смена статуса (отменённый заказ больше не меняем)
    if request.method == "POST" and order.status != "cancel":
        new_status = request.POST.get("status")

        # при отмене возвращаем товары на склад
        if new_status == "cancel":
            for item in order.items.all():
                if item.product:
                    item.product.stock = item.product.stock + item.qty
                    item.product.save()

        order.status = new_status
        order.save()
        messages.success(request, "Статус заказа изменён")
        return redirect("staff_order", id=order.id)

    return render(request, "staff/order.html", {"order": order, "statuses": Order.STATUSES})


@login_required
def staff_products(request):
    if not request.user.is_staff:
        return redirect("catalog")

    products = Product.objects.all()
    return render(request, "staff/products.html", {"products": products})


@login_required
def staff_product_add(request):
    if not request.user.is_staff:
        return redirect("catalog")

    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Товар добавлен")
            return redirect("staff_products")
    else:
        form = ProductForm()

    return render(request, "staff/product_form.html", {"form": form, "title": "Новый товар"})


@login_required
def staff_product_edit(request, id):
    if not request.user.is_staff:
        return redirect("catalog")

    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Товар сохранён")
            return redirect("staff_products")
    else:
        form = ProductForm(instance=product)

    return render(request, "staff/product_form.html", {"form": form, "title": "Изменить товар"})


@login_required
def staff_product_delete(request, id):
    if not request.user.is_staff:
        return redirect("catalog")

    product = get_object_or_404(Product, id=id)
    product.delete()
    messages.success(request, "Товар удалён")
    return redirect("staff_products")


# Отчёт о продажах

def get_report(days):
    # заказы за последние days дней, кроме отменённых
    date_from = timezone.now() - timedelta(days=days)
    orders = Order.objects.filter(created_at__gte=date_from).exclude(status="cancel")

    # выручка
    revenue = 0
    for order in orders:
        revenue = revenue + order.total

    # сколько штук каждого товара продали
    sold = {}
    for order in orders:
        for item in order.items.all():
            if item.name in sold:
                sold[item.name] = sold[item.name] + item.qty
            else:
                sold[item.name] = item.qty

    # сортируем товары по количеству продаж и берём первые 10
    top = sorted(sold.items(), key=lambda x: x[1], reverse=True)[:10]

    return orders, revenue, top, date_from


@login_required
def staff_report(request):
    if not request.user.is_staff:
        return redirect("catalog")

    # период: неделя, месяц или квартал
    days = int(request.GET.get("days", 30))
    orders, revenue, top, date_from = get_report(days)

    count = len(orders)
    if count > 0:
        average = revenue // count
    else:
        average = 0

    return render(request, "staff/report.html", {
        "days": days,
        "count": count,
        "revenue": revenue,
        "average": average,
        "top": top,
        "date_from": date_from,
    })


@login_required
def staff_report_excel(request):
    if not request.user.is_staff:
        return redirect("catalog")

    days = int(request.GET.get("days", 30))
    orders, revenue, top, date_from = get_report(days)

    wb = Workbook()

    # лист 1: все заказы за период
    sheet = wb.active
    sheet.title = "Заказы"
    sheet.append(["Отчёт за последние " + str(days) + " дн."])
    sheet.append(["Заказов", len(orders)])
    sheet.append(["Выручка, ₽", revenue])
    sheet.append([])
    sheet.append(["№", "Дата", "Покупатель", "Телефон", "Статус", "Сумма, ₽"])
    for order in orders:
        date = timezone.localtime(order.created_at).strftime("%d.%m.%Y")
        sheet.append([order.id, date, order.name, order.phone, order.get_status_display(), order.total])

    # лист 2: популярные товары
    sheet2 = wb.create_sheet("Популярные товары")
    sheet2.append(["Товар", "Продано, шт."])
    for name, qty in top:
        sheet2.append([name, qty])

    # ширина колонок
    sheet.column_dimensions["C"].width = 20
    sheet.column_dimensions["D"].width = 20
    sheet2.column_dimensions["A"].width = 35

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="report.xlsx"'
    wb.save(response)
    return response
