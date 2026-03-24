from django.db import migrations


AIRPORTS = (
    ("ATH", "Athens", "Athens International Airport", "Greece"),
    ("BCN", "Barcelona", "Barcelona El Prat Airport", "Spain"),
    ("BER", "Berlin", "Berlin Brandenburg Airport", "Germany"),
    ("BGY", "Bergamo", "Il Caravaggio International Airport", "Italy"),
    ("BLQ", "Bologna", "Bologna Guglielmo Marconi Airport", "Italy"),
    ("BTS", "Bratislava", "M. R. Stefanik Airport", "Slovakia"),
    ("BUD", "Budapest", "Budapest Ferenc Liszt International Airport", "Hungary"),
    ("CGN", "Cologne", "Cologne Bonn Airport", "Germany"),
    ("CIA", "Rome", "Ciampino Airport", "Italy"),
    ("CRL", "Brussels", "Brussels South Charleroi Airport", "Belgium"),
    ("DTM", "Dortmund", "Dortmund Airport", "Germany"),
    ("DUB", "Dublin", "Dublin Airport", "Ireland"),
    ("EMA", "Nottingham", "East Midlands Airport", "United Kingdom"),
    ("FCO", "Rome", "Leonardo da Vinci Airport", "Italy"),
    ("GDN", "Gdansk", "Gdansk Lech Walesa Airport", "Poland"),
    ("KIV", "Chisinau", "Chisinau International Airport", "Moldova"),
    ("KRK", "Krakow", "John Paul II Krakow-Balice Airport", "Poland"),
    ("KTW", "Katowice", "Katowice Airport", "Poland"),
    ("LTN", "London", "London Luton Airport", "United Kingdom"),
    ("MAD", "Madrid", "Adolfo Suarez Madrid-Barajas Airport", "Spain"),
    ("MLA", "Malta", "Malta International Airport", "Malta"),
    ("MXP", "Milan", "Milan Malpensa Airport", "Italy"),
    ("NAP", "Naples", "Naples International Airport", "Italy"),
    ("OPO", "Porto", "Francisco Sa Carneiro Airport", "Portugal"),
    ("OTP", "Bucharest", "Henri Coanda International Airport", "Romania"),
    ("PRG", "Prague", "Vaclav Havel Airport Prague", "Czech Republic"),
    ("SOF", "Sofia", "Sofia Airport", "Bulgaria"),
    ("STN", "London", "London Stansted Airport", "United Kingdom"),
    ("TSF", "Venice", "Treviso Airport", "Italy"),
    ("VIE", "Vienna", "Vienna International Airport", "Austria"),
    ("VNO", "Vilnius", "Vilnius Airport", "Lithuania"),
    ("WAW", "Warsaw", "Warsaw Chopin Airport", "Poland"),
    ("WMI", "Warsaw", "Warsaw Modlin Airport", "Poland"),
)


def seed_airports(apps, schema_editor):
    airport_model = apps.get_model("airports", "Airport")
    for iata_code, city_name, airport_name, country_name in AIRPORTS:
        airport_model.objects.update_or_create(
            iata_code=iata_code,
            defaults={
                "city_name": city_name,
                "airport_name": airport_name,
                "country_name": country_name,
                "is_active": True,
            },
        )


def remove_airports(apps, schema_editor):
    airport_model = apps.get_model("airports", "Airport")
    airport_model.objects.filter(iata_code__in=[row[0] for row in AIRPORTS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("airports", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_airports, remove_airports),
    ]
