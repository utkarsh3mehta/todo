# Generated by Django 2.2.2 on 2019-06-12 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('handover', '0013_auto_20190605_1619'),
    ]

    operations = [
        migrations.AlterField(
            model_name='handover',
            name='ticketno',
            field=models.BigIntegerField(blank=True, db_column='ticketNo', null=True),
        ),
    ]
