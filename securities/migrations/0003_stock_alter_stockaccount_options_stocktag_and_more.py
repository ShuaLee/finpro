# Generated by Django 5.1.6 on 2025-03-05 11:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('securities', '0002_stockaccount_delete_stockportfolio'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('exchange', models.CharField(max_length=100)),
                ('current_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('currency', models.CharField(max_length=10)),
                ('dividends', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('sector', models.CharField(blank=True, max_length=100, null=True)),
                ('country', models.CharField(blank=True, max_length=100, null=True)),
                ('stock_type', models.CharField(choices=[('stock', 'Stock'), ('etf', 'ETF')], default='stock', max_length=20)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='stockaccount',
            options={'verbose_name': 'Stock Account', 'verbose_name_plural': 'Stock Accounts'},
        ),
        migrations.CreateModel(
            name='StockTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('stock_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_tags', to='securities.stockaccount')),
            ],
        ),
        migrations.AddField(
            model_name='stockaccount',
            name='tags',
            field=models.ManyToManyField(related_name='portfolios', to='securities.stocktag'),
        ),
    ]
