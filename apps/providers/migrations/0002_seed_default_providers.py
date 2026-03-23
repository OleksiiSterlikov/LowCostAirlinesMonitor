from django.db import migrations


DEFAULT_PROVIDER_DEFINITIONS = (
    {
        "code": "ryanair",
        "name": "Ryanair",
        "adapter_path": "apps.providers.adapters.ryanair.RyanairAdapter",
        "website_url": "https://www.ryanair.com/",
        "config_json": {},
        "is_active": True,
    },
    {
        "code": "wizzair",
        "name": "Wizz Air",
        "adapter_path": "apps.providers.adapters.wizzair.WizzAirAdapter",
        "website_url": "https://wizzair.com/",
        "config_json": {},
        "is_active": True,
    },
)


def seed_default_providers(apps, schema_editor):
    airline_provider = apps.get_model("providers", "AirlineProvider")
    for provider_definition in DEFAULT_PROVIDER_DEFINITIONS:
        airline_provider.objects.update_or_create(
            code=provider_definition["code"],
            defaults={
                "name": provider_definition["name"],
                "is_active": provider_definition["is_active"],
                "adapter_path": provider_definition["adapter_path"],
                "website_url": provider_definition["website_url"],
                "config_json": provider_definition["config_json"],
            },
        )


def remove_default_providers(apps, schema_editor):
    airline_provider = apps.get_model("providers", "AirlineProvider")
    airline_provider.objects.filter(
        code__in=[provider_definition["code"] for provider_definition in DEFAULT_PROVIDER_DEFINITIONS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("providers", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_providers, remove_default_providers),
    ]
