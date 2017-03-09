# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-09 14:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('world', '0022_npc_origin'),
    ]

    operations = [
        migrations.AddField(
            model_name='npc',
            name='skill_fighting',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='npc',
            name='trained_soldier',
            field=models.BooleanField(default=None),
        ),
    ]
