FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# ключ тут нужен только чтобы запустилась команда collectstatic
RUN DJANGO_SECRET_KEY=build-only DB_ENGINE=sqlite python manage.py collectstatic --noinput -v0 \
    && mkdir -p /app/media && useradd --create-home app && chown -R app /app
USER app

EXPOSE 8000
ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-"]
