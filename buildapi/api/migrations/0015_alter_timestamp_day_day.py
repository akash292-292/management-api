# Generated by Django 3.2.23 on 2023-11-13 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_alter_timestamp_day_day'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timestamp_day',
            name='day',
            field=models.IntegerField(null=True),
        ),
    ]
