# Generated by Django 3.2.23 on 2023-11-14 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_alter_timestamp_day_day'),
    ]

    operations = [
        migrations.CreateModel(
            name='report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('store_id', models.TextField(max_length=1000)),
                ('uptime_last_hour', models.IntegerField()),
                ('uptime_last_day', models.IntegerField()),
                ('update_last_week', models.IntegerField()),
                ('downtime_last_hour', models.IntegerField()),
                ('downtime_last_day', models.IntegerField()),
                ('downtime_last_week', models.IntegerField()),
            ],
        ),
    ]
