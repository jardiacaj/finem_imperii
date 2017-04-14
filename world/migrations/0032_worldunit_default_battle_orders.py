# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-13 12:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('battle', '0029_auto_20170413_1259'),
        ('world', '0031_auto_20170410_1629'),
    ]

    operations = [
        migrations.AddField(
            model_name='worldunit',
            name='default_battle_orders',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='battle.Order'),
        ),
    ]