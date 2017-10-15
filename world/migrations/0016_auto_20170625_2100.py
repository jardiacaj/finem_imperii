# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-25 19:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('world', '0015_settlement_public_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='last_activation_time',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='character',
            name='paused',
            field=models.BooleanField(default=False),
        ),
    ]