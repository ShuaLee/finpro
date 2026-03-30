from django.db import migrations


def drop_legacy_account_type_on_asset_type_schemas(apps, schema_editor):
    Schema = apps.get_model("schemas", "Schema")
    Schema.objects.filter(asset_type__isnull=False).exclude(account_type__isnull=True).update(account_type=None)


class Migration(migrations.Migration):

    dependencies = [
        ("schemas", "0002_asset_type_scoped_schemas"),
    ]

    operations = [
        migrations.RunPython(
            drop_legacy_account_type_on_asset_type_schemas,
            migrations.RunPython.noop,
        ),
    ]
