# Generated by Django 5.1.7 on 2025-03-29 21:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('portfolio', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SelfManagedAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_name', models.CharField(default='Self Managed Account', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=10, unique=True)),
                ('currency', models.CharField(blank=True, max_length=10)),
                ('is_etf', models.BooleanField(default=False)),
                ('stock_exchange', models.CharField(blank=True, max_length=50, null=True)),
                ('dividend_rate', models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True)),
                ('last_price', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='StockHolding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=10)),
                ('shares', models.DecimalField(decimal_places=4, max_digits=15)),
                ('purchase_price', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('custom_data', models.JSONField(blank=True, default=dict)),
                ('stock', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='securities.stock')),
                ('stock_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='securities.selfmanagedaccount')),
            ],
            options={
                'unique_together': {('stock_account', 'ticker')},
            },
        ),
        migrations.AddField(
            model_name='selfmanagedaccount',
            name='stocks',
            field=models.ManyToManyField(blank=True, related_name='self_managed_accounts', through='securities.StockHolding', to='securities.stock'),
        ),
        migrations.CreateModel(
            name='StockPortfolio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('custom_columns', models.JSONField(blank=True, default=dict)),
                ('portfolio', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='stock_portfolio', to='portfolio.portfolio')),
            ],
        ),
        migrations.AddField(
            model_name='selfmanagedaccount',
            name='stock_portfolio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='self_managed_accounts', to='securities.stockportfolio'),
        ),
        migrations.CreateModel(
            name='StockTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sub_tags', to='securities.stocktag')),
                ('stock_holding', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_tags', to='securities.stockholding')),
            ],
        ),
    ]
