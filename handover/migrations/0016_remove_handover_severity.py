# Generated by Django 2.2.2 on 2019-06-18 22:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('handover', '0015_auto_20190618_2144'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='handover',
            name='severity',
        ),
    ]