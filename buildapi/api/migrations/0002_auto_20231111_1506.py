# Generated by Django 3.2.23 on 2023-11-11 09:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Store_Details',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('store_id', models.TextField(max_length=100)),
                ('timezone_str', models.CharField(max_length=100)),
            ],
        ),
        migrations.DeleteModel(
            name='Store_Deatils',
        ),
    ]