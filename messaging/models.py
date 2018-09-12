from django.db import models
from django.urls.base import reverse
from django.utils.html import format_html


class ServerMOTD(models.Model):
    class Meta:
        ordering = ['display_order']

    title = models.TextField()
    html_content = models.TextField()
    display_order = models.SmallIntegerField()
    draft = models.BooleanField(default=True)

    def get_html_content(self):
        return format_html(self.html_content)

    def __str__(self):
        return self.title


class CharacterMessage(models.Model):
    class Meta:
        ordering = ['creation_time']

    content = models.TextField()
    creation_time = models.DateTimeField(auto_now_add=True)
    creation_turn = models.IntegerField()
    sender = models.ForeignKey(
        'character.Character',
        models.SET_NULL,
        related_name='messages_sent', blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    link = models.TextField(blank=True, null=True)

    def get_nice_recipient_list(self):
        return (
                [group.organization for group in
                 self.messagerecipientgroup_set.all()]
                +
                [recipient.character for recipient in
                 self.messagerecipient_set.filter(group=None)]
        )

    def get_post_recipient_list(self):
        return (
                ["organization_{}".format(group.organization.id) for group in
                 self.messagerecipientgroup_set.all()]
                +
                ["character_{}".format(recipient.character.id) for recipient in
                 self.messagerecipient_set.filter(group=None)]
        )


class MessageRecipientGroup(models.Model):
    class Meta:
        unique_together = (
            ("message", "organization"),
        )

    message = models.ForeignKey(CharacterMessage, models.CASCADE)
    organization = models.ForeignKey('organization.Organization',
                                     models.CASCADE)


class MessageRecipient(models.Model):
    class Meta:
        unique_together = (
            ("message", "character"),
        )
        index_together = (
            ("character", "read"),
        )

    message = models.ForeignKey(CharacterMessage, models.CASCADE)
    group = models.ForeignKey(
        MessageRecipientGroup, models.CASCADE,
        blank=True, null=True
    )
    read = models.BooleanField(default=False)
    character = models.ForeignKey('character.Character', models.CASCADE)
    favourite = models.BooleanField(default=False)

    def get_mark_read_url(self):
        return reverse('messaging:mark_read',
                       kwargs={'recipient_id': self.id})

    def get_mark_favourite_url(self):
        return reverse('messaging:mark_favourite',
                       kwargs={'recipient_id': self.id})


class MessageRelationship(models.Model):
    class Meta:
        unique_together = (
            ("from_character", "to_character"),
        )

    from_character = models.ForeignKey('character.Character', models.CASCADE)
    to_character = models.ForeignKey(
        'character.Character', models.CASCADE,
        related_name='message_relationships_to'
    )
