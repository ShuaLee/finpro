# Generated by Django 5.1.7 on 2025-03-13 01:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='individualportfolio',
            name='name',
        ),
    ]
