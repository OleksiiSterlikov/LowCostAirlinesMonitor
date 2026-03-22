# Low-Cost Ticket Price Monitor

Стартовий skeleton репозиторію для застосунку моніторингу цін на квитки low-cost авіакомпаній.

## Stack
- Python 3.12
- Django 5
- MySQL 8
- Celery
- Redis
- Docker Compose
- Pytest

## Основні можливості
- моніторинг цін для 1 пасажира без багажу
- валюта відображення: EUR
- збереження всіх знайдених варіантів
- користувачі можуть бути створені адміністратором або самостійно реєструватися з подальшим підтвердженням адміністратором
- обов'язкова зміна тимчасового пароля при першому вході
- email/Telegram нотифікації при зміні ціни
- provider-based архітектура для Wizz Air, Ryanair та інших авіакомпаній

## Швидкий старт
```bash
python -m venv .venv
.venv\Scripts\activate
cp .env.example .env
docker compose up --build
```

Після запуску:
- Django: http://localhost:9000
- Admin: http://localhost:9000/admin

## Корисні команди
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web pytest
```

## Структура
- `src/` — Django project settings, Celery bootstrap, urls
- `apps/accounts/` — користувачі, реєстрація, профіль, approval flow
- `apps/providers/` — airline providers, adapters, provider registry
- `apps/searches/` — user search subscriptions, fare snapshots, price change detection
- `apps/notifications/` — email/Telegram нотифікації
- `apps/dashboard/` — UI кабінету користувача
- `docs/` — AI-friendly документація для Codex/розробки

## Важливо
Це skeleton, а не готовий production scraper. Для інтеграцій з провайдерами потрібно буде:
- реалізувати конкретні adapter-інтеграції
- врахувати rate limits, anti-bot, CAPTCHA, legal/ToS обмеження
- додати retry/backoff/proxy/observability
