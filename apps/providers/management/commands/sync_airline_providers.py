from django.core.management.base import BaseCommand

from apps.providers.services import sync_default_providers


class Command(BaseCommand):
    help = "Create or update the default airline provider records."

    def handle(self, *args, **options):
        created, updated = sync_default_providers()
        self.stdout.write(
            self.style.SUCCESS(
                f"Airline providers synchronized. Created: {created}. Updated: {updated}."
            )
        )
