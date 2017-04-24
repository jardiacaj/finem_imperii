from django.contrib import admin

from battle.battle_init import start_battle
from battle.battle_tick import battle_tick, battle_turn
from battle.models import Battle, BattleFormation

admin.site.register(BattleFormation)


def start(modeladmin, request, queryset):
    for battle in queryset.all():
        start_battle(battle)
start.short_description = "Start battle"


def tick_action(modeladmin, request, queryset):
    for battle in queryset.all():
        battle_tick(battle)
tick_action.short_description = "Do tick"


def turn_action(modeladmin, request, queryset):
    for battle in queryset.all():
        battle_turn(battle)
turn_action.short_description = "Do turn"


@admin.register(Battle)
class WorldAdmin(admin.ModelAdmin):
    actions = [start, tick_action, turn_action]
