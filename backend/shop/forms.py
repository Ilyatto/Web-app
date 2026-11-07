from django import forms

from .models import Product


# Форма добавления и изменения товара для сотрудника
class ProductForm(forms.ModelForm):
    # первый пункт списка «не выбрано» вместо прочерков
    category = forms.ChoiceField(label="Категория", choices=[("", "не выбрано")] + Product.CATEGORIES)

    class Meta:
        model = Product
        fields = ["name", "category", "brand", "price", "stock", "description", "socket", "ram_type", "power"]
