# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-11-15 22:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('world', '0004_auto_20161113_2127'),
    ]

    operations = [
        migrations.AddField(
            model_name='worldregion',
            name='y_pos',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]