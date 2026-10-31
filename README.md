# IlyattoPC — онлайн-продажа и сборка ПК

Веб-приложение на Django + PostgreSQL + Redis

## Возможности
- **Каталог**: 8 категорий, поиск, сортировка, карточка товара с характеристиками и остатком.
- **Конфигуратор**: проверка совместимости (сокет, тип памяти, форм-фактор, длина видеокарты, высота кулера, мощность БП), расчёт нагрузки, готовые сборки. Несовместимую сборку нельзя положить в корзину.
- **Корзина и заказ**: оформление (курьер 500 ₽ или самовывоз), история и статусы заказов, отмена.
- **Раздел сотрудников** `/staff/`: сводка, обработка заказов с резервом товара, счёт и накладная, склад, товары, отчёты (Excel и PDF), клиенты.

## Роли (по ТЗ)
| Роль | Что доступно |
|---|---|
| Гость | Каталог, поиск, страница товара, вход и регистрация |
| Покупатель | + конфигуратор, сохранённые сборки, корзина, заказы, профиль |
| Менеджер | Сводка, обработка заказов, клиенты, складские остатки, счёт и накладная |
| Администратор | Всё, что может менеджер, + товары (добавление, изменение, удаление) и отчёты |

Статусы заказа: Новый → Подтверждён → Собран → Отправлен → Выполнен (или Отменён).
Товар списывается с остатка, когда менеджер подтверждает заказ; при отмене возвращается.

Назначить роль: `python manage.py set_role email@example.com manager` (роли: `customer`, `manager`, `admin`)
или в админке Django `/admin/` → «Профили». Суперпользователь Django всегда администратор.

## Что хранится где
**PostgreSQL** — все постоянные данные: пользователи и роли, товары, сборки, заказы и история их обработки, копия сессий.

**Redis** — быстрые и временные данные:

| Ключ | Тип | Назначение |
|---|---|---|
| `pcshop:cart:<владелец>` | HASH | корзина |
| `pcshop:build:<владелец>` | HASH | черновик сборки в конфигураторе |
| `pcshop:popular` | ZSET | рейтинг популярных товаров для главной |
| `pcshop:rl:login:<ip>:<email>` | STRING + TTL | 5 неудачных входов → блокировка на 10 минут |
| кэш Django `catalog:all` | — | кэш каталога, сбрасывается при изменении товара |
| сессии | — | читаются из Redis, копия в PostgreSQL |

Проверка подключения к обоим: http://127.0.0.1:8000/health/

---

## 1. Установка на Windows

### PostgreSQL
1. Установите PostgreSQL 16 с https://www.postgresql.org/download/windows/ (в комплекте есть pgAdmin). Запомните пароль пользователя `postgres`.
2. Создайте пользователя и базу. В **PowerShell** (в Git Bash `psql` не умеет спрашивать пароль):
   ```powershell
   & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE USER pcshop WITH PASSWORD 'ваш_пароль' CREATEDB;"
   & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE DATABASE pcshop OWNER pcshop;"
   ```
   Или в pgAdmin: Login/Group Roles → Create → имя `pcshop`, пароль, право «Create databases»; затем Databases → Create → `pcshop`, владелец `pcshop`.
   Право `CREATEDB` нужно, чтобы запускать автотесты.

### Redis
- **Docker Desktop:** `docker run -d --name pcshop-redis -p 6379:6379 --restart unless-stopped redis:7-alpine`
- или **Memurai** (Redis для Windows): https://www.memurai.com/
- без Redis для разработки: в `.env` укажите `REDIS_URL=memory://`

### Приложение
```bash
cd ~/Desktop/pcshop
python -m venv .venv
source .venv/Scripts/activate          # в PowerShell: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                   # и заполните POSTGRES_PASSWORD
python manage.py migrate
python manage.py seed                  # каталог, готовые сборки и изображения товаров
python manage.py demo                  # по желанию: тестовые аккаунты и 120 заказов
python manage.py runserver
```
Сайт: http://127.0.0.1:8000/ · раздел сотрудников: http://127.0.0.1:8000/staff/

Демо-аккаунты (после `demo`):

| Роль | Логин | Пароль |
|---|---|---|
| Администратор | admin@ilyattopc.ru | Admin-2026 |
| Менеджер | manager@ilyattopc.ru | Manager-2026 |
| Покупатель | client@ilyattopc.ru | Client-2026 |

---

## 2. Рабочий запуск

`runserver` — только для разработки. Для настоящей работы в `.env`:
```ini
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=длинный_случайный_ключ     # python -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_ALLOWED_HOSTS=shop.example.ru,127.0.0.1
```
Затем один раз собрать статику и запустить сервер приложения:

**Windows** (waitress):
```bash
python manage.py migrate
python manage.py collectstatic --noinput
waitress-serve --listen=0.0.0.0:8000 config.wsgi:application
```

**Linux** (gunicorn):
```bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

CSS и JS раздаёт само приложение (WhiteNoise) — отдельный веб-сервер для статики не нужен.
Первого администратора создайте без интерактивного ввода (работает и в Git Bash):
```bash
DJANGO_SUPERUSER_USERNAME=admin@ilyattopc.ru DJANGO_SUPERUSER_EMAIL=admin@ilyattopc.ru \
DJANGO_SUPERUSER_PASSWORD='надёжный_пароль' python manage.py createsuperuser --noinput
```

### HTTPS
Если сайт открывается по https через nginx, Caddy или хостинг, добавьте в `.env`:
```ini
DJANGO_HTTPS=1
DJANGO_CSRF_TRUSTED_ORIGINS=https://shop.example.ru
```
Это включит защищённые cookie, переадресацию на https и HSTS. Проверка настроек: `python manage.py check --deploy`.

### Docker (PostgreSQL + Redis + приложение)
```bash
cp .env.example .env      # заполните DJANGO_SECRET_KEY, POSTGRES_PASSWORD, DJANGO_ALLOWED_HOSTS, DJANGO_DEBUG=0
docker compose up -d --build
```
Миграции применяются при каждом старте. Демо-данные при первом запуске: `SEED_DEMO=1` в `.env` (потом уберите).
Администратор: `docker compose exec web python manage.py createsuperuser`.
Данные PostgreSQL и Redis хранятся в томах `pgdata` и `redisdata` и переживают перезапуск.

### Резервная копия базы
```bash
pg_dump -U pcshop -h localhost -Fc pcshop > pcshop.dump          # сохранить
pg_restore -U pcshop -h localhost -d pcshop --clean pcshop.dump  # восстановить
```
В Docker: `docker compose exec db pg_dump -U pcshop -Fc pcshop > pcshop.dump`

---

## Тесты
```bash
python manage.py test shop
```
Тесты создают временную базу в PostgreSQL (поэтому пользователю нужно право `CREATEDB`) и используют Redis в памяти.

## Структура
```
config/settings.py        настройки: PostgreSQL, Redis, безопасность, статика (всё через .env)
shop/models.py            Product, Build, Order, OrderItem, OrderEvent, Profile (роль)
shop/roles.py             роли и проверка доступа
shop/orders_service.py    жизненный цикл заказа и резерв товаров
shop/compat.py            правила совместимости
shop/redis_store.py       корзина, черновик сборки, популярное, лимит входа
shop/views.py             витрина и покупатель
shop/staff_views.py       раздел сотрудников и отчёты
shop/management/commands  seed, add_photos, demo, set_role, import_sqlite
shop/seed_images/         стандартные изображения товаров
shop/static/shop/         app.css и app.js
templates/                шаблоны страниц
Dockerfile, docker-compose.yml, docker-entrypoint.sh
```
