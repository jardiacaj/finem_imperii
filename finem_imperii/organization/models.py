import json

from django.db import models
from django.contrib.auth.models import User
from django.urls.base import reverse

from world.models import Tile, Character


class Organization(models.Model):
    DEMOCRATIC = 'democratic'  # decisions are voted among members
    DISTRIBUTED = 'distributed'  # decisions can be taken by each member
    DECISION_TAKING_CHOICES = (
        (DEMOCRATIC, DEMOCRATIC),
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
        descendants = list(self.owned_organizations.all())
        if including_self:
            descendants.append(self)
        for child in descendants:
            descendants += child.get_all_descendants()
        return descendants

    def get_membership_including_descendants(self):
        members = list(self.character_members.all())
        for child in self.owned_organizations.all():
            members += child.get_membership_including_descendants()
        return members

    def character_can_use_capabilities(self, character):
        if character in self.character_members.all():
            return True
        for member_organization in self.organization_members.all():
            if member_organization.leader and member_organization.leader.is_position and character in member_organization.organization_members.all():
                return True
            if member_organization.is_position and character in member_organization.organization_members.all():
                return True
        return False

    def character_is_member(self, character):
        if character in self.character_members.all():
            return True
        for member_organization in self.organization_members.all():
            if character in member_organization.member_set.all():
                return True
        return False

    def get_open_proposals(self):
        return CapabilityProposal.objects.filter(capability__applying_to=self, closed=False)

    def get_all_controlled_tiles(self):
        return Tile.objects.filter(controlled_by__in=self.get_all_descendants(including_self=True)).all()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organization:view', kwargs={'organization_id': self.id})


class Capability(models.Model):
    BAN = 'ban'
    POLICY_DOCUMENT = 'policy'
    CONSCRIPT = 'conscript'

    TYPE_CHOICES = (
        (BAN, 'ban'),
        (POLICY_DOCUMENT, 'write policy and law'),
        (CONSCRIPT, 'conscript trops'),
    )

    organization = models.ForeignKey(Organization)
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    applying_to = models.ForeignKey(Organization, related_name='capabilities_to_this')
    stemming_from = models.ForeignKey('Capability', null=True, blank=True, related_name='transfers')

    def get_absolute_url(self):
        return reverse('organization:capability', kwargs={'capability_id': self.id})

    def create_proposal(self, character, proposal_dict):
        proposal = CapabilityProposal.objects.create(
            proposing_character=character,
            capability=self,
            proposal_json=json.dumps(proposal_dict),
            vote_end_turn=self.organization.world.current_turn + 2,
        )
        if self.organization.is_position or self.organization.decision_taking == Organization.DISTRIBUTED:
            proposal.execute()
        else:
            proposal.issue_vote(character, CapabilityVote.YEA)

    def is_passive(self):
        return self.type in (self.CONSCRIPT, )


class CapabilityProposal(models.Model):
    proposing_character = models.ForeignKey(Character)
    capability = models.ForeignKey(Capability)
    proposal_json = models.TextField()
    vote_end_turn = models.IntegerField()
    executed = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)

    def execute(self):
        proposal = json.loads(self.proposal_json)
        if self.capability.type == Capability.POLICY_DOCUMENT:
            if proposal['new']:
                document = PolicyDocument(organization=self.capability.applying_to)
            else:
                document = PolicyDocument.objects.get(id=proposal['document_id'])

            if proposal['delete']:
                document.delete()
            else:
                document.title = proposal['title']
                document.body = proposal['body']
                document.public = 'public' in proposal.keys()
                document.last_modified_turn = self.capability.organization.world.current_turn
                document.save()
        else:
            raise Exception("Executing ")
        self.executed = True
        self.closed = True
        self.save()

    def issue_vote(self, character, vote):
        CapabilityVote.objects.create(
            proposal=self,
            voter=character,
            vote=vote
        )
        self.execute_if_enough_votes()

    def execute_if_enough_votes(self):
        pass


class CapabilityVote(models.Model):
    YEA = 'yea'
    NAY = 'nay'
    INVALID = 'invalid'
    VOTE_CHOICES = (
        (YEA, YEA),
        (NAY, NAY),
        (INVALID, INVALID),
    )

    proposal = models.ForeignKey(CapabilityProposal)
    voter = models.ForeignKey(Character)
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)


class PolicyDocument(models.Model):
    organization = models.ForeignKey(Organization)
    parent = models.ForeignKey('PolicyDocument', related_name='children', null=True, blank=True)
    public = models.BooleanField(default=False)
    title = models.TextField(max_length=100)
    body = models.TextField()
    last_modified_turn = models.IntegerField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('organization:document', kwargs={'document_id': self.id})
