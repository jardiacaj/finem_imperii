# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-22 14:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0024_auto_20170322_1541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='positionelection',
            name='closed',
            field=models.BooleanField(default=False),
        ),
    ]
