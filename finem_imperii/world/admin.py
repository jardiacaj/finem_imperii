from django.contrib import admin

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
        world.initialize()
initialize_world.short_description = "Initialize world"


@admin.register(World)
class WorldAdmin(admin.ModelAdmin):
    actions = [initialize_world]
