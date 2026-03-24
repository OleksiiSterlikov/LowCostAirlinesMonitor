from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Airport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("iata_code", models.CharField(max_length=3, unique=True)),
                ("city_name", models.CharField(max_length=128)),
                ("airport_name", models.CharField(max_length=255)),
                ("country_name", models.CharField(max_length=128)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["city_name", "airport_name", "iata_code"],
            },
        ),
    ]
