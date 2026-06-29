from django.db import migrations, models


WIZZAIR_CONFIG_DEFAULTS = {
    "min_poll_interval_seconds": 600,
    "playwright_persistent_context_enabled": True,
    "playwright_user_data_dir": "/tmp/wizzair-playwright-profile",
    "playwright_storage_state_path": "/tmp/wizzair-playwright-storage-state.json",
}


def add_wizzair_runtime_defaults(apps, schema_editor):
    airline_provider = apps.get_model("providers", "AirlineProvider")
    provider = airline_provider.objects.filter(code="wizzair").first()
    if provider is None:
        return

    config_json = provider.config_json or {}
    changed = False
    for key, value in WIZZAIR_CONFIG_DEFAULTS.items():
        if key not in config_json:
            config_json[key] = value
            changed = True

    if changed:
        provider.config_json = config_json
        provider.save(update_fields=["config_json", "updated_at"])


def remove_wizzair_runtime_defaults(apps, schema_editor):
    airline_provider = apps.get_model("providers", "AirlineProvider")
    provider = airline_provider.objects.filter(code="wizzair").first()
    if provider is None:
        return

    config_json = provider.config_json or {}
    changed = False
    for key in WIZZAIR_CONFIG_DEFAULTS:
        if key in config_json:
            config_json.pop(key)
            changed = True

    if changed:
        provider.config_json = config_json
        provider.save(update_fields=["config_json", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("providers", "0004_provider_runtime_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="airlineprovider",
            name="last_polled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(add_wizzair_runtime_defaults, remove_wizzair_runtime_defaults),
    ]
