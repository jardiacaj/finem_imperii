from django.db import models


class ServerMOTD(models.Model):
    class Meta:
        ordering = ['display_order']

    title = models.TextField()
    html_content = models.TextField()
    display_order = models.SmallIntegerField()
    draft = models.BooleanField(default=True)


class CharacterNotification(models.Model):
    class Meta:
        ordering = ['creation_time']

    TRAVEL = 'travel'
    CATEGORY_CHOICES = (
        (TRAVEL, TRAVEL),
    )

    character = models.ForeignKey('world.Character')
    content = models.TextField()
    category = models.CharField(max_length=15)
    creation_time = models.DateTimeField(auto_now_add=True)
    creation_turn = models.IntegerField()
    read = models.BooleanField(default=False)


class Message(models.Model):
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    turn = models.IntegerField()
    sender = models.ForeignKey('world.Character', related_name='messages_sent')


class MessageReceiverGroup(models.Model):
    message = models.ForeignKey(Message)
    organization = models.ForeignKey('organization.Organization')


class MessageReceiver(models.Model):
    message = models.ForeignKey(Message)
    group = models.ForeignKey(MessageReceiverGroup, blank=True, null=True)
    read = models.BooleanField(default=False)
    character = models.ForeignKey('world.Character')
