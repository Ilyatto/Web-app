from django.urls import path

from . import views

urlpatterns = [
    # каталог
    path("", views.catalog, name="catalog"),
    path("product/<int:id>/", views.product_page, name="product"),
    path("builder/", views.builder, name="builder"),

    # вход и регистрация
    path("register/", views.register_page, name="register"),
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_page, name="logout"),

    # корзина и заказы покупателя
    path("cart/", views.cart_page, name="cart"),
    path("cart/add/<int:id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:id>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.my_orders, name="my_orders"),

    # раздел сотрудника
    path("staff/", views.staff_orders, name="staff_orders"),
    path("staff/order/<int:id>/", views.staff_order, name="staff_order"),
    path("staff/products/", views.staff_products, name="staff_products"),
    path("staff/products/add/", views.staff_product_add, name="staff_product_add"),
    path("staff/products/<int:id>/edit/", views.staff_product_edit, name="staff_product_edit"),
    path("staff/products/<int:id>/delete/", views.staff_product_delete, name="staff_product_delete"),
    path("staff/report/", views.staff_report, name="staff_report"),
    path("staff/report/excel/", views.staff_report_excel, name="staff_report_excel"),
]
