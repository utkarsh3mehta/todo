# Generated by Django 2.2 on 2019-06-05 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('handover', '0012_auto_20190605_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='userpassword',
            field=models.CharField(db_column='userpassword', max_length=150),
        ),
    ]
