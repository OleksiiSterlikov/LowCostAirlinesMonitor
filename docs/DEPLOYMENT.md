# DEPLOYMENT.md

## Мінімальна production схема
- Nginx reverse proxy
- Django app через Gunicorn
- Celery worker
- Celery beat
- MySQL
- Redis

## Потрібно додати перед production
- `DEBUG=0`
- коректний `ALLOWED_HOSTS`
- зовнішній SMTP
- реальний Telegram bot token
- HTTPS
- резервне копіювання БД
- monitoring/alerting/log aggregation
- DB migrations step у CI/CD
