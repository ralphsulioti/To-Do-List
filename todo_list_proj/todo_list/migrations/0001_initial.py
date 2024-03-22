# Generated by Django 5.0.2 on 2024-03-21 21:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='List',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('list_name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_date_added', models.DateTimeField(verbose_name='date added')),
                ('item_descr', models.CharField(max_length=200)),
                ('item_done', models.BooleanField()),
                ('list_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='todo_list.list')),
            ],
        ),
        migrations.AddField(
            model_name='list',
            name='user_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='todo_list.user'),
        ),
    ]
