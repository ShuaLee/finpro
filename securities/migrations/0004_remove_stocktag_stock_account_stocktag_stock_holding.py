# Generated by Django 5.1.7 on 2025-03-11 01:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('securities', '0003_stock_currency_stock_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stocktag',
            name='stock_account',
        ),
        migrations.AddField(
            model_name='stocktag',
            name='stock_holding',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stock_tags', to='securities.stockholding'),
        ),
    ]
