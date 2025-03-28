# Generated by Django 5.1.7 on 2025-03-28 01:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('securities', '0012_alter_stockholding_unique_together_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='stockholding',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='stockholding',
            constraint=models.UniqueConstraint(condition=models.Q(('stock__isnull', False)), fields=('stock_account', 'stock'), name='unique_stock_per_account'),
        ),
        migrations.AddConstraint(
            model_name='stockholding',
            constraint=models.UniqueConstraint(condition=models.Q(('custom_ticker__isnull', False)), fields=('stock_account', 'custom_ticker'), name='unique_custom_ticker_per_account'),
        ),
    ]
