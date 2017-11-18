# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-18 23:44
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organization', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('unit', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Building',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.SmallIntegerField(default=1, help_text='Go from 1 to 5')),
                ('type', models.CharField(choices=[('grain field', 'grain field'), ('residence', 'residence'), ('granary', 'granary'), ('prison', 'prison'), ('guild', 'guild')], max_length=15)),
                ('quantity', models.IntegerField(default=1)),
                ('field_production_counter', models.IntegerField(default=0)),
                ('owner', models.ForeignKey(blank=True, help_text="NULL means 'owned by local population'", null=True, on_delete=django.db.models.deletion.CASCADE, to='organization.Organization')),
            ],
        ),
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('cash', models.IntegerField(default=0)),
                ('hours_in_turn_left', models.IntegerField(default=360)),
                ('profile', models.CharField(choices=[('commander', 'commander'), ('trader', 'trader'), ('bureaucrat', 'bureaucrat')], max_length=20)),
                ('last_activation_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('paused', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('grain', 'grain bushels'), ('cart', 'transport carts')], max_length=20)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='world.Building')),
                ('owner_character', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='world.Character')),
            ],
        ),
        migrations.CreateModel(
            name='NPC',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('male', models.BooleanField()),
                ('able', models.BooleanField()),
                ('age_months', models.IntegerField()),
                ('trained_soldier', models.BooleanField(default=None)),
                ('skill_fighting', models.IntegerField()),
                ('wound_status', models.SmallIntegerField(choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)], default=0)),
                ('hunger', models.PositiveIntegerField(default=0)),
            ],
            options={
                'base_manager_name': 'stats_manager',
            },
            managers=[
                ('stats_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Settlement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('population', models.IntegerField(default=0)),
                ('population_default', models.IntegerField()),
                ('x_pos', models.IntegerField()),
                ('z_pos', models.IntegerField()),
                ('public_order', models.IntegerField(default=1000, help_text='0-1000, shown as %')),
                ('guilds_setting', models.CharField(choices=[('prohibit guilds', 'prohibit guilds'), ('restrict guilds', 'restrict guilds'), ('keep guilds', 'keep guilds'), ('promote guilds', 'promote guilds')], default='keep guilds', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Tile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('x_pos', models.IntegerField()),
                ('y_pos', models.FloatField()),
                ('z_pos', models.IntegerField()),
                ('type', models.CharField(choices=[('plains', 'plains'), ('forest', 'forest'), ('shore', 'shore'), ('deepsea', 'deep sea'), ('mountain', 'mountain')], max_length=15)),
                ('controlled_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organization.Organization')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='world.Region')),
            ],
        ),
        migrations.CreateModel(
            name='TileEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('conquest', 'conquest')], db_index=True, max_length=20)),
                ('counter', models.IntegerField(blank=True, null=True)),
                ('start_turn', models.IntegerField()),
                ('end_turn', models.IntegerField(blank=True, null=True)),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='organization.Organization')),
                ('tile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='world.Tile')),
            ],
        ),
        migrations.CreateModel(
            name='World',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField()),
                ('initialized', models.BooleanField(default=False)),
                ('current_turn', models.IntegerField(default=0)),
                ('blocked_for_turn', models.BooleanField(default=False, help_text='True during turn processing')),
            ],
        ),
        migrations.AddField(
            model_name='tile',
            name='world',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='world.World'),
        ),
        migrations.AddField(
            model_name='settlement',
            name='tile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='world.Tile'),
        ),
        migrations.AddField(
            model_name='region',
            name='world',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='world.World'),
        ),
        migrations.AddField(
            model_name='npc',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='world.Settlement'),
        ),
        migrations.AddField(
            model_name='npc',
            name='origin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offspring', to='world.Settlement'),
        ),
        migrations.AddField(
            model_name='npc',
            name='residence',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='resident', to='world.Building'),
        ),
        migrations.AddField(
            model_name='npc',
            name='unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='soldier', to='unit.WorldUnit'),
        ),
        migrations.AddField(
            model_name='npc',
            name='workplace',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='worker', to='world.Building'),
        ),
        migrations.AddField(
            model_name='character',
            name='location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='world.Settlement'),
        ),
        migrations.AddField(
            model_name='character',
            name='oath_sworn_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='organization.Organization'),
        ),
        migrations.AddField(
            model_name='character',
            name='owner_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='character',
            name='travel_destination',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='travellers_heading', to='world.Settlement'),
        ),
        migrations.AddField(
            model_name='character',
            name='world',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='world.World'),
        ),
        migrations.AddField(
            model_name='building',
            name='settlement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='world.Settlement'),
        ),
        migrations.AlterUniqueTogether(
            name='tile',
            unique_together=set([('world', 'x_pos', 'z_pos')]),
        ),
        migrations.AlterUniqueTogether(
            name='region',
            unique_together=set([('world', 'name')]),
        ),
        migrations.AlterIndexTogether(
            name='npc',
            index_together=set([('residence', 'hunger')]),
        ),
    ]
