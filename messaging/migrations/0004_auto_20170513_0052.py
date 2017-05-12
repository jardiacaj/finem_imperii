# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-12 22:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0003_charactermessage_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='charactermessage',
            name='category',
            field=models.CharField(blank=True, choices=[('travel', 'travel'), ('conquest', 'conquest'), ('turn', 'new turn'), ('proposal', 'action proposal')], max_length=20, null=True),
        ),
    ]
