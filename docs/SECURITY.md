# SECURITY.md

## Основні принципи
- секрети лише через env
- логування без витоку PII та credentials
- CSRF увімкнений
- password validation увімкнена
- обов'язкова зміна тимчасового пароля
- самореєстрація не означає автоматичний доступ до системи

## Що доробити
- rate limiting для login/register
- account lockout / brute-force protection
- email verification при self-registration
- audit log для admin approval actions
- шифрування чутливих інтеграційних налаштувань
