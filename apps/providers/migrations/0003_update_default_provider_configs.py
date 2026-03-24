from django.db import migrations


DEFAULT_PROVIDER_UPDATES = (
    {
        "code": "ryanair",
        "config_json": {
            "base_url": "https://www.ryanair.com/api/farfnd/v4",
            "market": "en-gb",
            "language": "en",
            "timeout": 30.0,
            "max_price": 1000,
            "fare_identity_keys": [
                "outbound.flightKey",
                "outbound.departureDate",
            ],
        },
    },
    {
        "code": "wizzair",
        "config_json": {
            "base_url": "https://be.wizzair.com/9.13.0/Api",
            "timeout": 30.0,
            "fare_identity_keys": [
                "flightNumber",
                "departureDate",
                "departureDateTime",
            ],
        },
    },
)


def update_default_provider_configs(apps, schema_editor):
    airline_provider = apps.get_model("providers", "AirlineProvider")
    for provider_update in DEFAULT_PROVIDER_UPDATES:
        airline_provider.objects.filter(code=provider_update["code"]).update(
            config_json=provider_update["config_json"]
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("providers", "0002_seed_default_providers"),
    ]

    operations = [
        migrations.RunPython(update_default_provider_configs, noop_reverse),
    ]
