# Generated by Django 3.2.23 on 2023-11-11 11:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_delete_menu_hours'),
    ]

    operations = [
        migrations.CreateModel(
            name='menu_hours',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('store_id', models.TextField(max_length=100)),
                ('day', models.IntegerField()),
                ('start_time_local', models.TextField(max_length=100)),
                ('end_time_local', models.TextField(max_length=100)),
            ],
        ),
    ]
