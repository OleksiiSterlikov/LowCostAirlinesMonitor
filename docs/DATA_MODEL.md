# DATA_MODEL.md

## Основні сутності
- `User`
- `RegistrationRequest`
- `AirlineProvider`
- `SearchSubscription`
- `FareSnapshot`
- `PriceChangeEvent`

## Ключові зв'язки
- User 1:N SearchSubscription
- SearchSubscription 1:N FareSnapshot
- SearchSubscription 1:N PriceChangeEvent
- AirlineProvider 1:N FareSnapshot
- AirlineProvider 1:N PriceChangeEvent
