from django.db import models
from django.urls.base import reverse


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
    class Meta:
        unique_together = (
            ("message", "organization"),
        )

    message = models.ForeignKey(CharacterMessage)
    organization = models.ForeignKey('organization.Organization')


class MessageReceiver(models.Model):
    class Meta:
        unique_together = (
            ("message", "character"),
        )

    message = models.ForeignKey(CharacterMessage)
    group = models.ForeignKey(MessageReceiverGroup, blank=True, null=True)
    read = models.BooleanField(default=False)
    character = models.ForeignKey('world.Character')
    favourite = models.BooleanField(default=False)

    def get_mark_read_url(self):
        return reverse('messaging:mark_read', kwargs={'receiver_id': self.id})

    def get_mark_favourite_url(self):
        return reverse('messaging:mark_favourite', kwargs={'receiver_id': self.id})


class MessageRelationship(models.Model):
    class Meta:
        unique_together = (
            ("from_character", "to_character"),
        )

    from_character = models.ForeignKey('world.Character')
    to_character = models.ForeignKey('world.Character', related_name='message_relationships_to')
