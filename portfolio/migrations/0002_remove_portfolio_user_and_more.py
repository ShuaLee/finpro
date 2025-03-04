# Generated by Django 5.1.6 on 2025-03-04 11:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_profile_role'),
        ('portfolio', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='portfolio',
            name='user',
        ),
        migrations.AddField(
            model_name='portfolio',
            name='asset_manager_profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='multiple_portfolios', to='core.profile'),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='individual_profile',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.profile'),
        ),
        migrations.AlterField(
            model_name='portfolio',
            name='name',
            field=models.CharField(default='Portfolio', max_length=255),
        ),
    ]
