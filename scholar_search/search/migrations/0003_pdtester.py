# Generated by Django 5.1.3 on 2024-11-27 05:10

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("search", "0002_umtester_delete_userinfo"),
    ]

    operations = [
        migrations.CreateModel(
            name="pdTester",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.TextField()),
                ("summary", models.TextField()),
                ("authors", models.TextField()),
                ("published", models.DateTimeField()),
                ("url", models.TextField()),
            ],
        ),
    ]
