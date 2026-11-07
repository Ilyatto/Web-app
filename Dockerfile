# Образ с Python
FROM python:3.12-slim

# папка проекта внутри контейнера
WORKDIR /app

# ставим библиотеки
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# копируем весь проект (backend и frontend)
COPY . .

# команды Django запускаются из папки backend
WORKDIR /app/backend

EXPOSE 8000

# создаём таблицы, заполняем базу и запускаем сайт
CMD python manage.py migrate && python manage.py seed && python manage.py runserver 0.0.0.0:8000
