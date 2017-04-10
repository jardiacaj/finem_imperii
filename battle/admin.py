from django.contrib import admin

from battle.battle_init import start_battle
from battle.models import Battle, BattleFormation

admin.site.register(BattleFormation)

def start(modeladmin, request, queryset):
    for battle in queryset.all():
        start_battle(battle)
start.short_description = "Start battle"


@admin.register(Battle)
class WorldAdmin(admin.ModelAdmin):
    actions = [start, ]
