import json

from django.db import models, transaction
from django.contrib.auth.models import User
from django.urls.base import reverse
from django.utils.html import escape

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

    INHERITED = 'inherited'
    ELECTED = 'elected'
    POSITION_TYPE_CHOICES = (
        (INHERITED, INHERITED),
        (ELECTED, ELECTED),
    )

    world = models.ForeignKey('world.World')
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=6, default="FFFFFF", help_text="Format: RRGGBB (hex)")
    description = models.TextField()
    is_position = models.BooleanField()
    position_type = models.CharField(max_length=15, choices=POSITION_TYPE_CHOICES, blank=True, default='')
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
    current_election = models.ForeignKey('PositionElection', blank=True, null=True, related_name='+')
    last_election = models.ForeignKey('PositionElection', blank=True, null=True, related_name='+')
    heir_first = models.ForeignKey(Character, blank=True, null=True, related_name='first_heir_to')
    heir_second = models.ForeignKey(Character, blank=True, null=True, related_name='second_heir_to')

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
            if (
                            member_organization.leader and
                            member_organization.leader.is_position and
                            character in member_organization.organization_members.all()
            ):
                return True
            if member_organization.is_position and character in member_organization.organization_members.all():
                return True
        return False

    def organizations_character_can_apply_capabilities_to_this_with(self, character, capability_type):
        result = []
        capabilities = Capability.objects.filter(applying_to=self, type=capability_type)
        for capability in capabilities:
            if capability.organization.character_is_member(character):
                result.append(capability.organization)
        return result

    def character_is_member(self, character):
        if character in self.character_members.all():
            return True
        for member_organization in self.organization_members.all():
            if character in member_organization.member_set.all():
                return True
        return False

    def is_part_of_violence_monopoly(self):
        return (
            True if self.violence_monopoly
            else False if not self.owner
            else self.owner.is_part_of_violence_monopoly()
        )

    def get_open_proposals(self):
        return CapabilityProposal.objects.filter(capability__applying_to=self, closed=False)

    def get_all_controlled_tiles(self):
        return Tile.objects.filter(controlled_by__in=self.get_all_descendants(including_self=True)).all()

    def external_capabilities_to_this(self):
        return self.capabilities_to_this.exclude(organization=self)

    def get_position_ocuppier(self):
        if not self.is_position or not self.character_members.exists():
            return None
        return list(self.character_members.all())[0]

    @transaction.atomic
    def convoke_elections(self, months_to_election=6):
        if not self.is_position:
            raise Exception("Elections only work for positions")
        election = PositionElection.objects.create(
            position=self,
            turn=self.world.current_turn + months_to_election
        )
        self.current_election = election
        self.save()
        if self.get_position_ocuppier() is not None:
            PositionCandidate.objects.create(
                election=election,
                candidate=self.get_position_ocuppier(),
                description="Auto-generated candidacy for incumbent character."
            )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organization:view', kwargs={'organization_id': self.id})

    def get_html_name(self):
        if self.violence_monopoly:
            template = '<span style="color: #{color}">◼</span>{name}<span style="color: #{color}">◼</span>'
        elif self.leaded_organizations.filter(violence_monopoly=True).exists():
            template = '<span style="color: #{color}">◢</span>{name}<span style="color: #{color}">◣</span>'
        elif self.is_part_of_violence_monopoly():
            template = '<span style="color: #{color}">▼</span>{name}<span style="color: #{color}">▼</span>'
        elif self.leaded_organizations.exists():
            template = '<span style="color: #{color}">◮</span>{name}<span style="color: #{color}">◭</span>'
        elif not self.owner:
            template = '<span style="color: #{color}">◨</span>{name}<span style="color: #{color}">◧</span>'
        else:
            template = '<span style="color: #{color}">◞</span>{name}<span style="color: #{color}">◟</span>'

        return template.format(
            name=escape(self.name),
            color=escape(self.color)
        )

    def get_html_link(self):
        return '<a href="{}">{}</a>'.format(self.get_absolute_url(), self.get_html_name())


class PositionElection(models.Model):
    position = models.ForeignKey(Organization)
    turn = models.IntegerField()
    closed = models.BooleanField(default=False)
    winner = models.ForeignKey('PositionCandidate', blank=True, null=True)


class PositionCandidate(models.Model):
    class Meta:
        unique_together = (
            ("election", "candidate"),
        )
    election = models.ForeignKey(PositionElection)
    candidate = models.ForeignKey(Character)
    description = models.TextField()


class PositionElectionVote(models.Model):
    class Meta:
        unique_together = (
            ("election", "voter"),
        )
    election = models.ForeignKey(PositionElection)
    voter = models.ForeignKey(Character)
    candidate = models.ForeignKey(PositionCandidate, blank=True, null=True)


class Capability(models.Model):
    BAN = 'ban'
    POLICY_DOCUMENT = 'policy'
    CONSCRIPT = 'conscript'
    DIPLOMACY = 'diplomacy'
    DISSOLVE = 'dissolve'
    MANAGE_SUBORGANIZATIONS = 'suborganizations'
    SECEDE = 'secede'
    MEMBERSHIPS = 'memberships'
    HEIR = 'heir'
    ELECT = 'elect'
    CANDIDACY = 'candidacy'
    CONVOKE_ELECTIONS = 'convoke elections'

    TYPE_CHOICES = (
        (BAN, 'ban'),
        (POLICY_DOCUMENT, 'write policy and law'),
        (DIPLOMACY, 'diplomacy'),
        (CONSCRIPT, 'conscript troops'),
        (DISSOLVE, 'dissolve'),
        (MANAGE_SUBORGANIZATIONS, 'manage subordinate organizations'),
        (SECEDE, 'secede'),
        (MEMBERSHIPS, 'memberships'),
        (HEIR, 'set heir'),
        (ELECT, 'elect'),
        (CANDIDACY, 'present candidacy'),
        (CONVOKE_ELECTIONS, 'convoke elections'),
    )

    organization = models.ForeignKey(Organization)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
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

        elif self.capability.type == Capability.BAN:
            character_to_ban = Character.objects.get(id=proposal['character_id'])
            self.capability.applying_to.character_members.remove(character_to_ban)

            leader_organization = self.capability.applying_to.leader
            if leader_organization and character_to_ban in leader_organization.character_members.all():
                leader_organization.character_members.remove(character_to_ban)

        elif self.capability.type == Capability.CONVOKE_ELECTIONS:
            if self.capability.applying_to.current_election is None:
                months_to_election = proposal['months_to_election']
                self.capability.applying_to.convoke_elections(months_to_election)

        else:
            raise Exception("Executing unknown capability type '{}'".format(self.capability.type))

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

    def delete_disallowed_votes(self):
        for vote in self.capabilityvote_set.all():
            if not self.capability.organization.character_is_member(vote.voter):
                vote.delete()

    def execute_if_enough_votes(self):
        self.delete_disallowed_votes()
        possible_votes = self.votes_possible()
        if self.votes_yea().count() > possible_votes / 2:
            self.execute()

    def votes_possible(self):
        return self.capability.organization.character_members.count()

    def execute_if_majority(self):
        self.delete_disallowed_votes()
        if self.votes_yea().count() > self.votes_nay().count():
            self.execute()

    def votes_yea(self):
        return self.capabilityvote_set.filter(vote=CapabilityVote.YEA)

    def votes_nay(self):
        return self.capabilityvote_set.filter(vote=CapabilityVote.NAY)

    def votes_invalid(self):
        return self.capabilityvote_set.filter(vote=CapabilityVote.INVALID)

    def get_absolute_url(self):
        return reverse('organization:proposal', kwargs={'proposal_id': self.id})


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
