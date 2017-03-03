from django.db import models
from django.contrib.auth.models import User

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

    world = models.ForeignKey('world.World')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    description = models.TextField()
    is_position = models.BooleanField()
    inherit_capabilities = models.BooleanField(
        help_text="If true, capabilities of parents and leader apply to this organization too"
    )
    parent = models.ForeignKey('Organization', null=True, blank=True, related_name='children')
    leader = models.ForeignKey('Organization', null=True, blank=True, related_name='leaded_organizations')
    violence_monopoly = models.BooleanField(default=False)
    decision_taking = models.CharField(max_length=15, choices=DECISION_TAKING_CHOICES)
    members = models.ManyToManyField('world.Character')

    def get_all_descendants(self, including_self=False):
        descendants = list(self.children.all())
        if including_self:
            descendants.append(self)
        for child in descendants:
            descendants += child.get_all_descendants()
        return descendants

    def get_membership_including_descendants(self):
        members = list(self.members.all())
        for child in self.children.all():
            members += child.get_membership_including_descendants()
        return members

    def get_all_controlled_tiles(self):
        return Tile.objects.filter(controlled_by__in=self.get_all_descendants(including_self=True)).all()

    def __str__(self):
        return self.name


class Capability(models.Model):
    ARREST_ORDER = 'arrest_order'
    BAN = 'ban'
    POLICY_DOCUMENT = 'policy'
    TYPE_CHOICES = (
        (ARREST_ORDER, ARREST_ORDER),
        (BAN, BAN),
        (POLICY_DOCUMENT, POLICY_DOCUMENT),
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
