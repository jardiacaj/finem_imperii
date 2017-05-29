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
    CONQUEST = 'conquest'
    TURN = 'turn'
    PROPOSAL = 'proposal'
    BATTLE = 'battle'
    POLICY = 'policy'
    BAN = 'ban'
    ELECTIONS = 'elections'
    DIPLOMACY = 'diplomacy'
    MILITARY_STANCE = 'military stance'
    BATTLE_FORMATION = 'battle formation'
    GUILDS = 'guilds'
    UNIT = 'unit'
    WELCOME = 'welcome'
    HEIR = 'heir'
    LEAVE = 'leaving'
    TAXES = 'taxes'
    NEWCOMER = 'newcomer'
    CATEGORY_CHOICES = (
        (TRAVEL, TRAVEL),
        (CONQUEST, CONQUEST),
        (TURN, "new turn"),
        (PROPOSAL, "action proposal"),
        (BATTLE, BATTLE),
        (POLICY, "policy and law"),
        (BAN, "ban"),
        (ELECTIONS, "elections"),
        (DIPLOMACY, "diplomacy"),
        (MILITARY_STANCE, "military stance"),
        (BATTLE_FORMATION, "battle formation"),
        (CONQUEST, "conquest"),
        (GUILDS, "conquest"),
        (UNIT, "unit"),
        (WELCOME, "welcome"),
        (HEIR, "heir"),
        (LEAVE, "leaving"),
        (TAXES, "taxes"),
        (NEWCOMER, "newcomer"),
    )

    content = models.TextField()
    creation_time = models.DateTimeField(auto_now_add=True)
    creation_turn = models.IntegerField()
    sender = models.ForeignKey(
        'world.Character', related_name='messages_sent', blank=True, null=True)
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)
    safe = models.BooleanField(default=False)
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

    message = models.ForeignKey(CharacterMessage)
    organization = models.ForeignKey('organization.Organization')


class MessageRecipient(models.Model):
    class Meta:
        unique_together = (
            ("message", "character"),
        )
        index_together = (
            ("character", "read"),
        )

    message = models.ForeignKey(CharacterMessage)
    group = models.ForeignKey(MessageRecipientGroup, blank=True, null=True)
    read = models.BooleanField(default=False)
    character = models.ForeignKey('world.Character')
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

    from_character = models.ForeignKey('world.Character')
    to_character = models.ForeignKey(
        'world.Character', related_name='message_relationships_to')
