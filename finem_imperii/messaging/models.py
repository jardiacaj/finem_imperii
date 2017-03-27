from django.db import models


class ServerMOTD(models.Model):
    class Meta:
        ordering = ['display_order']

    title = models.TextField()
    html_content = models.TextField()
    display_order = models.SmallIntegerField()
    draft = models.BooleanField(default=True)


class CharacterMessage(models.Model):
    class Meta:
        ordering = ['creation_time']

    TRAVEL = 'travel'
    CATEGORY_CHOICES = (
        (TRAVEL, TRAVEL),
    )

    content = models.TextField()
    creation_time = models.DateTimeField(auto_now_add=True)
    creation_turn = models.IntegerField()
    sender = models.ForeignKey('world.Character', related_name='messages_sent', blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)
    safe = models.BooleanField(default=False)


class MessageReceiverGroup(models.Model):
    message = models.ForeignKey(CharacterMessage)
    organization = models.ForeignKey('organization.Organization')


class MessageReceiver(models.Model):
    message = models.ForeignKey(CharacterMessage)
    group = models.ForeignKey(MessageReceiverGroup, blank=True, null=True)
    read = models.BooleanField(default=False)
    character = models.ForeignKey('world.Character')
