from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("providers", "0003_update_default_provider_configs"),
    ]

    operations = [
        migrations.AddField(
            model_name="airlineprovider",
            name="consecutive_failures",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="airlineprovider",
            name="cooldown_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="airlineprovider",
            name="last_error_message",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="airlineprovider",
            name="last_failure_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="airlineprovider",
            name="last_success_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
