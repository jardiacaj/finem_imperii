from django.contrib import admin

# Register your models here.
from character.models import Character


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'profile', 'owner_user', 'location')
    list_filter = ('world', )
