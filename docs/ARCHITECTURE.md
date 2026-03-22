# ARCHITECTURE.md

## Архітектурний підхід
Застосунок побудований як модульний Django monolith із фоновою обробкою через Celery.

## Компоненти
- Django web app: UI, admin, auth, profile management
- MySQL: основна transactional БД
- Redis: broker/result backend для Celery
- Celery worker: polling, notification dispatch, integration tasks
- Celery beat: плановий щогодинний запуск polling tasks

## Основні bounded contexts
- `accounts`: користувачі, approval, профілі, тимчасові паролі
- `providers`: довідник авіакомпаній та registry адаптерів
- `searches`: пошукові підписки, snapshots, price change events
- `notifications`: email/Telegram dispatch
- `dashboard`: кабінет користувача

## Data flow
1. Користувач створює subscription.
2. Щогодини Celery підбирає активні subscriptions.
3. Для кожного active provider завантажується adapter.
4. Adapter повертає список `FareOption`.
5. Кожен варіант зберігається у `FareSnapshot`.
6. Якщо ціна відрізняється від попередньої для того самого варіанта, створюється `PriceChangeEvent`.
7. Для price change event відправляється нотифікація.

## Provider extensibility
Через admin можна:
- увімкнути/вимкнути провайдера
- зберігати adapter path
- зберігати конфігурацію провайдера у JSON

Через код потрібно:
- додати конкретний adapter class
- забезпечити сумісність з `SearchQuery` і `FareOption`

## Обмеження skeleton
- немає migrations
- немає production hardening
- немає реальних scraper/integration реалізацій
- немає retries/circuit breaker/metrics
