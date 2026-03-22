# DEVELOPMENT.md

## Local setup
```bash
python -m venv .venv
.venv\Scripts\activate
cp .env.example .env
docker compose up --build
```

Local web URL: `http://localhost:9000`

## Команди
```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web pytest
```

## Рекомендований workflow
1. Оновити docs при зміні доменної моделі.
2. Додати/оновити model.
3. Згенерувати migrations.
4. Додати services/tasks/tests.
5. Лише потім доробити UI.

## Стиль коду
- тонкі views
- services для бізнес-логіки
- adapters для провайдерів
- Decimal для цін
- без прихованої логіки в signals, якщо цього можна уникнути
