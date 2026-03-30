from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portfolios", "0004_navigationstate"),
    ]

    operations = [
        migrations.AddField(
            model_name="navigationstate",
            name="accounts_collapsed",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="navigationstate",
            name="active_item_key",
            field=models.CharField(blank=True, default="portfolio", max_length=200),
        ),
        migrations.AddField(
            model_name="navigationstate",
            name="asset_types_collapsed",
            field=models.BooleanField(default=False),
        ),
    ]
