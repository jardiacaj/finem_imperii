# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-10-30 12:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('world', '0003_delete_unitorder'),
        ('battle', '0005_auto_20161030_1307'),
    ]

    operations = [
        migrations.AddField(
            model_name='battleunit',
            name='world_unit',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='world.WorldUnit'),
            preserve_default=False,
        ),
    ]