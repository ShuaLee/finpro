import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("schemas", "0002_asset_type_scoped_schemas"),
        ("accounts", "0004_account_level_restrictions"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="schema",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="accounts",
                to="schemas.schema",
                help_text="Optional account-level schema override.",
            ),
        ),
    ]
