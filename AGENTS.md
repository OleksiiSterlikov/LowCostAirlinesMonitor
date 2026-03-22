# AGENTS.md

## Мета проєкту
Побудувати web-застосунок для моніторингу цін на квитки low-cost авіакомпаній. Система повинна дозволяти користувачам створювати підписки на маршрути та періоди, зберігати всі знайдені варіанти цін, щогодини перевіряти ціни та надсилати сповіщення при зміні ціни.

## Основні бізнес-вимоги
1. Моніторинг для 1 пасажира без багажу.
2. Базова валюта — EUR.
3. Початкові провайдери: Wizz Air, Ryanair.
4. Нові авіакомпанії мають легко додаватися через provider-based architecture.
5. Адміністратор може створювати користувачів вручну.
6. Можлива самореєстрація, але з підтвердженням адміністратором.
7. При першому вході з тимчасовим паролем користувач повинен змінити пароль.
8. Користувач може редагувати власні дані в профілі.
9. Користувач створює пошук: origin, destination, date_from, date_to, канал сповіщення.
10. Пошуки зберігаються до скасування користувачем або завершення періоду.
11. Щогодини запускається poller, який опитує всі активні пошуки.
12. У разі зміни ціни користувач отримує email або Telegram повідомлення.
13. Необхідно зберігати всі знайдені варіанти, а не тільки найнижчу ціну.

## Роль Codex / AI-агента
AI-агент повинен:
- дотримуватись architecture decisions з цього репозиторію
- не ламати provider abstraction
- спершу оновлювати docs, якщо змінюється модель домену
- для нових інтеграцій додавати окремий adapter та тести
- не змішувати scraping logic з Django views
- не вбудовувати секрети в код або тести

## Coding rules
- Python 3.12+
- Django apps мають бути модульними й вузько відповідальними
- бізнес-логіка в services, orchestration у tasks, HTTP/UI у views
- будь-яка інтеграція авіакомпанії реалізується через `AirlineAdapter`
- provider config зберігати в БД через `AirlineProvider`
- усі ціни зберігати як Decimal
- часовий пояс: Europe/Kyiv
- не використовувати float для фінансів
- не писати scraping code прямо в model methods

## Очікувана структура для нових провайдерів
Для нового провайдера додавати:
1. adapter class у `apps/providers/adapters/`
2. tests для adapter/service layer
3. admin-config або seed для `AirlineProvider`
4. mapping полів raw response -> `FareOption`
5. error handling, retry/backoff, logging

## Безпека та відповідність
- перевіряти ToS та допустимість автоматизованого опитування
- враховувати rate limits
- використовувати throttling/backoff
- не логувати паролі, токени, cookies
- Telegram bot token лише через env
- email credentials лише через env

## Що робити далі після цього skeleton
1. Додати migrations.
2. Додати custom authentication backend для login by username/email.
3. Реалізувати approval workflow з admin actions.
4. Реалізувати real provider adapters.
5. Додати Celery retry policy, structured logging, observability.
6. Додати REST API або HTMX/UI enhancements.
7. Додати production deployment stack.
