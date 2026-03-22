from django.conf import settings
from django.core.mail import send_mail


class TelegramNotifier:
    def send(self, chat_id: str, message: str) -> None:
        # TODO: implement actual Telegram API call
        if not chat_id:
            return
        print(f"[TELEGRAM -> {chat_id}] {message}")


class EmailNotifier:
    def send(self, email: str, subject: str, message: str) -> None:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)


class NotificationDispatcher:
    def __init__(self) -> None:
        self.telegram = TelegramNotifier()
        self.email = EmailNotifier()

    def send_price_change(self, event) -> None:
        user = event.subscription.user
        subject = f"Зміна ціни: {event.subscription.origin} → {event.subscription.destination}"
        message = (
            f"Маршрут: {event.subscription.origin} → {event.subscription.destination}\n"
            f"Провайдер: {event.provider.name}\n"
            f"Дата: {event.outbound_date}\n"
            f"Стара ціна: {event.old_price} {event.currency}\n"
            f"Нова ціна: {event.new_price} {event.currency}"
        )
        if event.subscription.notify_via == "telegram":
            self.telegram.send(user.telegram_chat_id, message)
        else:
            self.email.send(user.email, subject, message)
