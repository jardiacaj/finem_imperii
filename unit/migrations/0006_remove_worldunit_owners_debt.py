# Generated by Django 2.1 on 2018-08-19 19:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('unit', '0005_auto_20180819_0036'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='worldunit',
            name='owners_debt',
        ),
    ]
