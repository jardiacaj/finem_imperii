from django.db import models
from django.contrib.auth.models import User
from django.urls.base import reverse

from world.models import Tile


class Organization(models.Model):
    DEMOCRATIC = 'democratic'  # decisions are voted among members
    AUTOCRATIC = 'autocratic'  # decisions are taken by leader
    DISTRIBUTED = 'distributed'  # decisions can be taken by each member
    DECISION_TAKING_CHOICES = (
        (DEMOCRATIC, DEMOCRATIC),
        (AUTOCRATIC, AUTOCRATIC),
        (DISTRIBUTED, DISTRIBUTED),
    )

    CHARACTER = 'character'
    ORGANIZATION = 'organization'
    MEMBERSHIP_TYPE_CHOICES = (
        (CHARACTER, CHARACTER),
        (ORGANIZATION, ORGANIZATION),
    )

    world = models.ForeignKey('world.World')
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_position = models.BooleanField()
    inherit_capabilities = models.BooleanField(
        help_text="If true, capabilities of parents and leader apply to this organization too"
    )
    owner = models.ForeignKey('Organization', null=True, blank=True, related_name='owned_organizations')
    leader = models.ForeignKey('Organization', null=True, blank=True, related_name='leaded_organizations')
    owner_and_leader_locked = models.BooleanField(
        help_text="If set, this organization will have always the same leader as it's owner."
    )
    violence_monopoly = models.BooleanField(default=False)
    decision_taking = models.CharField(max_length=15, choices=DECISION_TAKING_CHOICES)
    membership_type = models.CharField(max_length=15, choices=MEMBERSHIP_TYPE_CHOICES)
    character_members = models.ManyToManyField('world.Character')
    organization_members = models.ManyToManyField('Organization')
    election_period_months = models.IntegerField(default=0)
    last_election = models.IntegerField(default=0)

    def get_all_descendants(self, including_self=False):
        descendants = list(self.children.all())
        if including_self:
            descendants.append(self)
        for child in descendants:
            descendants += child.get_all_descendants()
        return descendants

    def get_membership_including_descendants(self):
        members = list(self.character_members.all())
        for child in self.children.all():
            members += child.get_membership_including_descendants()
        return members

    def get_all_controlled_tiles(self):
        return Tile.objects.filter(controlled_by__in=self.get_all_descendants(including_self=True)).all()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organization:view', kwargs={'organization_id': self.id})


class Capability(models.Model):
    ARREST_ORDER = 'arrest_order'
    BAN = 'ban'
    POLICY_DOCUMENT = 'policy'
    CONSCRIPT = 'conscript'

    TYPE_CHOICES = (
        (ARREST_ORDER, 'ordering arrests'),
        (BAN, 'banning'),
        (POLICY_DOCUMENT, 'writing policy and law'),
    )

    organization = models.ForeignKey(Organization)
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)


class OrganizationDecision(models.Model):
    pass


class PolicyDocument(models.Model):
    organization = models.ForeignKey(Organization)
    parent = models.ForeignKey('PolicyDocument')
    public = models.BooleanField(default=False)


class PolicyDocumentVersion(models.Model):
    document = models.ForeignKey(PolicyDocument)
    title = models.TextField()
    body = models.TextField()
    draft = models.BooleanField()
    proposal = models.BooleanField()
