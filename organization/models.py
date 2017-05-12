import json
import world.models
import world.templatetags.extra_filters

from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models.aggregates import Count
from django.urls.base import reverse
from django.utils.html import escape

from battle.models import BattleFormation


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
    barbaric = models.BooleanField(default=False)
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
    character_members = models.ManyToManyField('world.Character', blank=True)
    organization_members = models.ManyToManyField('Organization', blank=True)
    election_period_months = models.IntegerField(default=0)
    current_election = models.ForeignKey('PositionElection', blank=True, null=True, related_name='+')
    last_election = models.ForeignKey('PositionElection', blank=True, null=True, related_name='+')
    heir_first = models.ForeignKey('world.Character', blank=True, null=True, related_name='first_heir_to')
    heir_second = models.ForeignKey('world.Character', blank=True, null=True, related_name='second_heir_to')
    tax_countdown = models.SmallIntegerField(default=0)

    def get_descendants_list(self, including_self=False):
        descendants = list()
        if including_self:
            descendants.append(self)
        for child in self.owned_organizations.all():
            descendants += child.get_descendants_list(True)
        return descendants

    def get_membership_including_descendants(self):
        members = set(self.character_members.all())
        for child in self.owned_organizations.all():
            members |= child.get_membership_including_descendants()
        return members

    def character_can_use_capabilities(self, character):
        if character in self.character_members.all():
            return True

    def organizations_character_can_apply_capabilities_to_this_with(self, character, capability_type):
        result = []
        capabilities = Capability.objects.filter(applying_to=self, type=capability_type)
        for capability in capabilities:
            if capability.organization.character_can_use_capabilities(character):
                result.append(capability.organization)
        return result

    def character_is_member(self, character):
        return character in self.character_members.all()

    def get_violence_monopoly(self):
        if self.violence_monopoly:
            return self
        try:
            return self.leaded_organizations.get(violence_monopoly=True)
        except Organization.DoesNotExist:
            pass
        if self.owner:
            return self.owner.get_violence_monopoly()
        return False

    def conquestable_tiles(self):
        if not self.violence_monopoly:
            return None
        candidate_tiles = world.models.Tile.objects \
            .filter(world=self.world) \
            .exclude(controlled_by=self) \
            .exclude(type__in=(world.models.Tile.SHORE, world.models.Tile.DEEPSEA))
        result = []
        for tile in candidate_tiles:
            conquest_tile_event = tile.tileevent_set.filter(
                organization=self,
                type=world.models.TileEvent.CONQUEST,
                end_turn__isnull=True
            )
            conquering_units = tile.get_units()\
                .filter(owner_character__in=self.character_members.all())\
                .exclude(status=world.models.WorldUnit.NOT_MOBILIZED)
            if (
                conquering_units.exists() and not conquest_tile_event.exists()
            ):
                result.append(tile)
        return result

    def get_open_proposals(self):
        return CapabilityProposal.objects.filter(capability__organization=self, closed=False)

    def get_all_controlled_tiles(self):
        return world.models.Tile.objects.filter(controlled_by__in=self.get_descendants_list(including_self=True)).all()

    def external_capabilities_to_this(self):
        return self.capabilities_to_this.exclude(organization=self)

    def get_position_occupier(self):
        if not self.is_position or not self.character_members.exists():
            return None
        return list(self.character_members.all())[0]

    def get_relationship_to(self, organization):
        return OrganizationRelationship.objects.get_or_create(
            defaults={
                'relationship': (OrganizationRelationship.WAR
                                 if organization.barbaric or
                                 self.barbaric else
                                 OrganizationRelationship.PEACE)
            },
            from_organization=self,
            to_organization=organization
        )[0]

    def get_relationship_from(self, organization):
        return organization.get_relationship_to(self)

    def get_default_stance_to(self, state):
        return MilitaryStance.objects.get_or_create(
            from_organization=self,
            to_organization=state,
            region=None
        )[0]

    def get_region_stances_to(self, state):
        return MilitaryStance.objects.filter(
            from_organization=self,
            to_organization=state,
        ).exclude(region=None)

    def get_region_stance_to(self, state, region):
        return MilitaryStance.objects.get_or_create(
            from_organization=self,
            to_organization=state,
            region=region
        )[0]

    def get_default_formation_settings(self):
        try:
            return BattleFormation.objects.get(organization=self, battle=None)
        except BattleFormation.DoesNotExist:
            return BattleFormation.objects.create(
                organization=self,
                battle=None,
                formation=BattleFormation.LINE,
                element_size=2,
                spacing=2,
            )

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
        if self.get_position_occupier() is not None:
            PositionCandidacy.objects.create(
                election=election,
                candidate=self.get_position_occupier(),
                description="Auto-generated candidacy for incumbent character."
            )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organization:view', kwargs={'organization_id': self.id})

    def get_html_name(self):
        template = '{name}{icon}{suffix}'
        icon = self.get_bootstrap_icon()

        occupier = self.get_position_occupier()
        if occupier:
            suffix = '<small>{}</small>'.format(occupier.name)
        else:
            suffix = ''

        return template.format(
            name=escape(self.name),
            icon=icon,
            suffix=suffix
        )

    def get_bootstrap_icon(self):
        template = '<span style="color: #{color}" class="glyphicon glyphicon-{icon}" aria-hidden="true"></span>'
        if self.violence_monopoly and not self.barbaric:
            icon = "tower"
        elif self.violence_monopoly and self.barbaric:
            icon = "fire"
        elif self.leaded_organizations.filter(violence_monopoly=True).exists():
            icon = "king"
        elif self.get_violence_monopoly():
            icon = "knight"
        elif self.leaded_organizations.exists():
            icon = "menu-up"
        elif not self.owner:
            icon = "triangle-top"
        else:
            icon = "option-vertical"
        return template.format(
            icon=icon,
            color=escape(self.color),
        )

    def get_html_link(self):
        return '<a href="{}">{}</a>'.format(self.get_absolute_url(), self.get_html_name())


class PositionElection(models.Model):
    position = models.ForeignKey(Organization)
    turn = models.IntegerField()
    closed = models.BooleanField(default=False)
    winner = models.ForeignKey('PositionCandidacy', blank=True, null=True)

    def open_candidacies(self):
        return self.positioncandidacy_set.filter(retired=False)

    def last_turn_to_present_candidacy(self):
        return self.turn - 3

    def can_present_candidacy(self):
        return self.position.world.current_turn <= self.last_turn_to_present_candidacy()

    @transaction.atomic
    def resolve(self):
        max_votes = 0
        winners = []
        for candidacy in self.open_candidacies().all():
            votes = candidacy.positionelectionvote_set.count()
            if votes > max_votes:
                max_votes = votes
                winners = []
            if votes == max_votes:
                winners.append(candidacy)

        if len(winners) != 1:
            self.position.convoke_elections()
        else:
            winning_candidacy = winners[0]
            winning_candidate = winning_candidacy.candidate
            self.winner = winning_candidacy
            self.position.character_members.remove(self.position.get_position_occupier())
            self.position.character_members.add(winning_candidate)

        self.position.last_election = self
        self.position.current_election = None
        self.position.save()
        self.closed = True
        self.save()

    def get_results(self):
        return self.positioncandidacy_set.all().annotate(num_votes=Count('positionelectionvote'))\
            .order_by('-num_votes')

    def get_absolute_url(self):
        return reverse('organization:election', kwargs={'election_id': self.id})

    def __str__(self):
        return "{} election for {}".format(
            world.templatetags.extra_filters.nice_turn(self.turn),
            self.position
        )


class PositionCandidacy(models.Model):
    class Meta:
        unique_together = (
            ("election", "candidate"),
        )
    election = models.ForeignKey(PositionElection)
    candidate = models.ForeignKey('world.Character')
    description = models.TextField()
    retired = models.BooleanField(default=False)


class PositionElectionVote(models.Model):
    class Meta:
        unique_together = (
            ("election", "voter"),
        )
    election = models.ForeignKey(PositionElection)
    voter = models.ForeignKey('world.Character')
    candidacy = models.ForeignKey(PositionCandidacy, blank=True, null=True)


class Capability(models.Model):
    BAN = 'ban'
    POLICY_DOCUMENT = 'policy'
    CONSCRIPT = 'conscript'
    DIPLOMACY = 'diplomacy'
    MANAGE_SUBORGANIZATIONS = 'suborganizations'
    MEMBERSHIPS = 'memberships'
    HEIR = 'heir'
    ELECT = 'elect'
    CANDIDACY = 'candidacy'
    CONVOKE_ELECTIONS = 'convoke elections'
    MILITARY_STANCE = 'military stance'
    BATTLE_FORMATION = 'battle formation'
    CONQUEST = 'occupy region'
    TAKE_GRAIN = 'take grain'
    GUILDS = 'manage guilds'
    TAXES = 'manage taxation'

    TYPE_CHOICES = (
        (BAN, 'ban'),
        (POLICY_DOCUMENT, 'write policy and law'),
        (DIPLOMACY, 'conduct diplomacy'),
        (CONSCRIPT, 'conscript troops'),
        (MANAGE_SUBORGANIZATIONS, 'manage subordinate organizations'),
        (MEMBERSHIPS, 'manage memberships'),
        (HEIR, 'set heir'),
        (ELECT, 'elect'),
        (CANDIDACY, 'present candidacy'),
        (CONVOKE_ELECTIONS, 'convoke elections'),
        (MILITARY_STANCE, 'military orders'),
        (BATTLE_FORMATION, 'battle formation'),
        (CONQUEST, 'occupy region'),
        (TAKE_GRAIN, 'take grain'),
        (GUILDS, 'manage guilds'),
        (TAXES, 'manage taxation'),
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
        return self.type in (self.CONSCRIPT, self.TAKE_GRAIN, )

    def is_individual_action(self):
        return self.is_passive() or self.type in (self.ELECT, self.CANDIDACY)

    def __str__(self):
        return "{} can {} in {}{}".format(
            self.organization,
            self.get_type_display(),
            self.applying_to,
            "" if self.stemming_from is None else " (delegated by {})".format(
                self.stemming_from
            )
        )


class CapabilityProposal(models.Model):
    proposing_character = models.ForeignKey('world.Character')
    capability = models.ForeignKey(Capability)
    proposal_json = models.TextField()
    vote_end_turn = models.IntegerField()
    executed = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)

    def execute(self):
        proposal = self.get_proposal_json_content()
        if self.capability.type == Capability.POLICY_DOCUMENT:
            try:
                if proposal['new']:
                    document = PolicyDocument(organization=self.capability.applying_to)
                else:
                    document = PolicyDocument.objects.get(id=proposal['document_id'])

                if proposal['delete']:
                    document.delete()
                else:
                    document.title = proposal.get('title')
                    document.body = proposal.get('body')
                    document.public = proposal.get('public') is not None
                    document.last_modified_turn = self.capability.organization.world.current_turn
                    document.save()
            except PolicyDocument.DoesNotExist:
                pass

        elif self.capability.type == Capability.BAN:
            try:
                character_to_ban = world.models.Character.objects.get(
                    id=proposal['character_id']
                )
                self.capability.applying_to.character_members.remove(
                    character_to_ban
                )
                if character_to_ban.get_violence_monopoly() is None:
                    character_to_ban.world.get_barbaric_state().character_members.add(
                        character_to_ban
                    )
            except world.models.Character.DoesNotExist:
                pass

            leader_organization = self.capability.applying_to.leader
            if leader_organization and character_to_ban in leader_organization.character_members.all():
                leader_organization.character_members.remove(character_to_ban)

        elif self.capability.type == Capability.CONVOKE_ELECTIONS:
            if self.capability.applying_to.current_election is None:
                months_to_election = proposal['months_to_election']
                self.capability.applying_to.convoke_elections(months_to_election)

        elif self.capability.type == Capability.DIPLOMACY:
            try:
                target_organization = Organization.objects.get(id=proposal['target_organization_id'])
                target_relationship = proposal['target_relationship']
                changing_relationship = self.capability.applying_to.get_relationship_to(target_organization)
                reverse_relationship = changing_relationship.reverse_relation()
                action_type = proposal['type']
                if action_type == 'propose':
                    changing_relationship.desire(target_relationship)
                elif action_type == 'accept':
                    if reverse_relationship.desired_relationship == target_relationship:
                        changing_relationship.set_relationship(target_relationship)
                elif action_type == 'take back':
                    if changing_relationship.desired_relationship == target_relationship:
                        changing_relationship.desired_relationship = None
                        changing_relationship.save()
                elif action_type == 'refuse':
                    if reverse_relationship.desired_relationship == target_relationship:
                        reverse_relationship.desired_relationship = None
                        reverse_relationship.save()

            except Organization.DoesNotExist:
                pass

        elif self.capability.type == Capability.MILITARY_STANCE:
            try:
                target_organization = Organization.objects.get(id=proposal['target_organization_id'])
                if 'region_id' in proposal.keys():
                    region = world.models.Tile.objects.get(id=proposal['region_id'])
                    target_stance = self.capability.applying_to.get_region_stance_to(target_organization, region)
                else:
                    target_stance = self.capability.applying_to.get_default_stance_to(target_organization)
                target_stance.stance_type = proposal.get('target_stance')
                target_stance.save()
            except (world.models.Tile.DoesNotExist, Organization.DoesNotExist):
                pass

        elif self.capability.type == Capability.BATTLE_FORMATION:
            try:
                formation = BattleFormation.objects.get(organization=self.capability.applying_to, battle=None)
            except BattleFormation.DoesNotExist:
                formation = BattleFormation(organization=self.capability.applying_to, battle=None)
            formation.formation = proposal['formation']
            formation.spacing = proposal['spacing']
            formation.element_size = proposal['element_size']
            formation.save()

        elif self.capability.type == Capability.CONQUEST:
            try:
                tile = world.models.Tile.objects.get(id=proposal['tile_id'])
                if proposal['stop']:
                    tile_event = world.models.TileEvent.objects.get(
                        tile=tile,
                        organization=self.capability.applying_to,
                        end_turn__isnull=True
                    )
                    tile_event.end_turn = self.capability.applying_to.world.current_turn
                    tile_event.save()
                else:
                    if tile in self.capability.applying_to.conquestable_tiles():
                        world.models.TileEvent.objects.create(
                            tile=tile,
                            type=world.models.TileEvent.CONQUEST,
                            organization=self.capability.applying_to,
                            counter=0,
                            start_turn=self.capability.applying_to.world.current_turn
                        )
            except (world.models.Tile.DoesNotExist, world.models.TileEvent.DoesNotExist):
                pass

        elif self.capability.type == Capability.GUILDS:
            try:
                settlement = world.models.Settlement.objects.get(
                    id=proposal['settlement_id']
                )
                if (
                        (settlement.tile in
                         self.capability.applying_to.get_all_controlled_tiles())
                        and
                        (proposal['option'] in
                         [choice[0] for choice in world.models.Settlement
                                 .GUILDS_CHOICES])
                ):
                    settlement.guilds_setting = proposal['option']
                    settlement.save()
            except world.models.Settlement.DoesNotExist:
                pass

        else:
            raise Exception("Executing unknown capability action_type '{}'".format(self.capability.type))

        self.executed = True
        self.closed = True
        self.save()

    def get_proposal_json_content(self):
        return json.loads(self.proposal_json)

    def issue_vote(self, character, vote):
        CapabilityVote.objects.create(
            proposal=self,
            voter=character,
            vote=vote
        )
        self.execute_if_enough_votes()
        self.close_if_enough_votes()

    def delete_disallowed_votes(self):
        for vote in self.capabilityvote_set.all():
            if not self.capability.organization.character_is_member(vote.voter):
                vote.delete()

    def execute_if_enough_votes(self):
        self.delete_disallowed_votes()
        possible_votes = self.votes_possible()
        if self.votes_yea().count() > possible_votes / 2:
            self.execute()

    def close_if_enough_votes(self):
        self.delete_disallowed_votes()
        possible_votes = self.votes_possible()
        if self.votes_nay().count() > possible_votes / 2:
            self.closed = True
            self.save()

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
    voter = models.ForeignKey('world.Character')
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


class OrganizationRelationship(models.Model):
    class Meta:
        unique_together = (
            ("from_organization", "to_organization"),
        )

    PEACE = 'peace'
    WAR = 'war'
    BANNED = 'banned'
    FRIENDSHIP = 'friendship'
    DEFENSIVE_ALLIANCE = 'defensive alliance'
    ALLIANCE = 'alliance'
    RELATIONSHIP_CHOICES = (
        (PEACE, PEACE),
        (WAR, WAR),
        (BANNED, BANNED),
        (FRIENDSHIP, FRIENDSHIP),
        (DEFENSIVE_ALLIANCE, DEFENSIVE_ALLIANCE),
        (ALLIANCE, ALLIANCE),
    )

    RELATIONSHIP_LEVEL = {
        WAR: 0,
        BANNED: 0,
        PEACE: 1,
        FRIENDSHIP: 2,
        DEFENSIVE_ALLIANCE: 3,
        ALLIANCE: 5
    }

    from_organization = models.ForeignKey(Organization, related_name='relationships_stemming')
    to_organization = models.ForeignKey(Organization, related_name='relationships_receiving')
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, default=PEACE)
    desired_relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, blank=True, null=True)

    def reverse_relation(self):
        return self.to_organization.get_relationship_to(self.from_organization)

    @staticmethod
    def _get_badge_type(relationship):
        if relationship in (OrganizationRelationship.WAR, OrganizationRelationship.BANNED):
            return 'danger'
        elif relationship == OrganizationRelationship.FRIENDSHIP:
            return 'success'
        elif relationship in (OrganizationRelationship.DEFENSIVE_ALLIANCE, OrganizationRelationship.ALLIANCE):
            return 'info'
        else:
            return 'default'

    @staticmethod
    def _format_relationship(relationship, relationship_name):
        template = '<span class="label label-{badge_type}">{name}</span>'
        return template.format(
            name=relationship_name.capitalize(),
            badge_type=OrganizationRelationship._get_badge_type(relationship)
        )

    def get_relationship_html(self):
        return OrganizationRelationship._format_relationship(self.relationship, self.get_relationship_display())

    def get_desired_relationship_html(self):
        if self.desired_relationship is None:
            return OrganizationRelationship._format_relationship(
                'default',
                'None'
            )
        else:
            return OrganizationRelationship._format_relationship(
                self.desired_relationship,
                self.get_desired_relationship_display()
            )

    def is_proposal(self):
        return self.desired_relationship and self.desired_relationship != self.relationship

    @transaction.atomic
    def desire(self, target_relationship):
        if self.RELATIONSHIP_LEVEL[target_relationship] < self.RELATIONSHIP_LEVEL[self.relationship]:
            self.set_relationship(target_relationship)
        else:
            self.desired_relationship = target_relationship
            self.save()

    @transaction.atomic
    def set_relationship(self, target_relationship):
        self.relationship = target_relationship
        self.desired_relationship = None
        self.save()
        reverse_relation = self.reverse_relation()
        reverse_relation.relationship = target_relationship
        reverse_relation.desired_relationship = None
        reverse_relation.save()

    def default_military_stance(self):
        if self.relationship in (OrganizationRelationship.PEACE,):
            return MilitaryStance.DEFENSIVE
        if self.relationship in (OrganizationRelationship.WAR, OrganizationRelationship.BANNED):
            return MilitaryStance.AGGRESSIVE
        return MilitaryStance.AVOID_BATTLE

    def __str__(self):
        return "Relationship {} to {}".format(self.from_organization, self.to_organization)


class MilitaryStance(models.Model):
    class Meta:
        unique_together = (
            ("from_organization", "to_organization", "region"),
        )
    DEFAULT = 'default'
    AVOID_BATTLE = 'avoid battle'
    DEFENSIVE = 'defensive'
    AGGRESSIVE = 'aggressive'

    STANCE_CHOICES=(
        (DEFAULT, "automatic by diplomatic relationship"),
        (AVOID_BATTLE, AVOID_BATTLE),
        (DEFENSIVE, DEFENSIVE),
        (AGGRESSIVE, AGGRESSIVE),
    )

    from_organization = models.ForeignKey(Organization, related_name='mil_stances_stemming')
    to_organization = models.ForeignKey(Organization, related_name='mil_stances_receiving')
    region = models.ForeignKey('world.Tile', related_name='+', null=True, blank=True)
    stance_type = models.CharField(max_length=20, choices=STANCE_CHOICES, default=DEFAULT)

    def get_stance(self):
        if self.stance_type != MilitaryStance.DEFAULT:
            return self.stance_type
        if self.region:
            return self.from_organization.get_default_stance_to(self.to_organization).get_stance()
        else:
            return self.from_organization.get_relationship_to(self.to_organization).default_military_stance()

    def get_html_stance(self):
        stance = self.get_stance()
        if stance == MilitaryStance.DEFENSIVE:
            bootstrap_type = 'primary'
        elif stance == MilitaryStance.AGGRESSIVE:
            bootstrap_type = 'danger'
        elif stance == MilitaryStance.AVOID_BATTLE:
            bootstrap_type = 'info'
        else:
            bootstrap_type = 'default'

        return '<span class="label label-{bootstrap_type}">{stance}</span>'.format(
            bootstrap_type=bootstrap_type,
            stance =stance
        )
