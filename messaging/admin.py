from django.contrib import admin

from messaging.models import ServerMOTD, CharacterMessage, MessageRecipient, \
    MessageRecipientGroup, MessageRelationship


@admin.register(ServerMOTD)
class MOTDAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_order', 'draft')
    list_filter = ('draft', )

admin.site.register(CharacterMessage)
admin.site.register(MessageRecipient)
admin.site.register(MessageRecipientGroup)
admin.site.register(MessageRelationship)
