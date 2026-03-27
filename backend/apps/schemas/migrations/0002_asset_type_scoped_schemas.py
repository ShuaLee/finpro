from django.db import migrations, models
import django.db.models.deletion


def backfill_schema_asset_types(apps, schema_editor):
    Schema = apps.get_model("schemas", "Schema")

    for schema in Schema.objects.select_related("account_type").all():
        account_type = schema.account_type
        if not account_type:
            continue

        allowed_asset_type_ids = list(
            account_type.allowed_asset_types.values_list("id", flat=True)[:2]
        )
        if len(allowed_asset_type_ids) == 1:
            schema.asset_type_id = allowed_asset_type_ids[0]
            schema.save(update_fields=["asset_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_initial"),
        ("assets", "0002_initial"),
        ("schemas", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="schema",
            name="asset_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="schemas",
                to="assets.assettype",
            ),
        ),
        migrations.AlterField(
            model_name="schema",
            name="account_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="schemas",
                to="accounts.accounttype",
            ),
        ),
        migrations.AlterModelOptions(
            name="schema",
            options={"ordering": ["asset_type__slug", "account_type__slug"]},
        ),
        migrations.RunPython(backfill_schema_asset_types, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name="schema",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="schema",
            constraint=models.UniqueConstraint(
                condition=models.Q(asset_type__isnull=False),
                fields=("portfolio", "asset_type"),
                name="uniq_schema_per_portfolio_asset_type",
            ),
        ),
        migrations.AddConstraint(
            model_name="schema",
            constraint=models.UniqueConstraint(
                condition=models.Q(account_type__isnull=False),
                fields=("portfolio", "account_type"),
                name="uniq_schema_per_portfolio_account_type_legacy",
            ),
        ),
        migrations.AddConstraint(
            model_name="schema",
            constraint=models.CheckConstraint(
                condition=models.Q(asset_type__isnull=False)
                | models.Q(account_type__isnull=False),
                name="schema_requires_asset_type_or_account_type",
            ),
        ),
    ]
