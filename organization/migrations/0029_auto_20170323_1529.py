# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-23 14:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0028_auto_20170322_1708'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='PositionCandidate',
            new_name='PositionCandidacy',
        ),
        migrations.RenameField(
            model_name='positionelectionvote',
            old_name='candidate',
            new_name='candidacy',
        ),
        migrations.AlterField(
            model_name='organization',
            name='character_members',
            field=models.ManyToManyField(blank=True, to='world.Character'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='organization_members',
            field=models.ManyToManyField(blank=True, to='organization.Organization'),
        ),
    ]