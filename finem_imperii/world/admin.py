from django.contrib import admin

from world.initialization import WorldInitializer
from world.models import Region, Tile, Settlement, Building, NPC, Character, WorldUnit, World

admin.site.register(Region)
admin.site.register(Tile)
admin.site.register(Settlement)
admin.site.register(Building)
admin.site.register(NPC)
admin.site.register(Character)
admin.site.register(WorldUnit)


def initialize_world(modeladmin, request, queryset):
    for world in queryset.all():
        initializer = WorldInitializer(world)
        initializer.initialize()
initialize_world.short_description = "Initialize world"


def pass_turn(modeladmin, request, queryset):
    for world in queryset.all():
        world.pass_turn()
pass_turn.short_description = "Pass turn"


@admin.register(World)
class WorldAdmin(admin.ModelAdmin):
    actions = [pass_turn, initialize_world]
