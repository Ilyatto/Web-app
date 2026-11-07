# Команда python manage.py seed создаёт аккаунты сотрудника и покупателя.
# Товары добавляет сотрудник на сайте в разделе «Товары».
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(username="admin", password="admin123")

        if not User.objects.filter(username="client").exists():
            User.objects.create_user(username="client", password="client123")

        print("Готово! Сотрудник: admin / admin123, покупатель: client / client123")
