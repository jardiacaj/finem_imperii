from django.db import models, transaction
from django.urls import reverse
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

from mixins import AdminURLMixin
from organization.models import capability, election, relationship
import unit.models
import world.models
from battle.models import BattleFormation
from messaging import shortcuts


class Organization(models.Model, AdminURLMixin):
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

    world = models.ForeignKey('world.World', models.CASCADE)
    name = models.CharField(max_length=100)
    color = models.CharField(
        max_length=6, default="FFFFFF", help_text="Format: RRGGBB (hex)")
    barbaric = models.BooleanField(default=False)
    description = models.TextField()
    is_position = models.BooleanField()
    position_type = models.CharField(
        max_length=15, choices=POSITION_TYPE_CHOICES, blank=True, default='')
    owner = models.ForeignKey(
        'Organization', models.SET_NULL, null=True, blank=True,
        related_name='owned_organizations')
    leader = models.ForeignKey(
        'Organization', models.SET_NULL, null=True, blank=True,
        related_name='leaded_organizations')
    owner_and_leader_locked = models.BooleanField(
        help_text="If set, this organization will have always the same "
                  "leader as it's owner."
    )
    violence_monopoly = models.BooleanField(default=False)
    decision_taking = models.CharField(
        max_length=15, choices=DECISION_TAKING_CHOICES)
    membership_type = models.CharField(
        max_length=15, choices=MEMBERSHIP_TYPE_CHOICES)
    character_members = models.ManyToManyField(
        'character.Character', blank=True)
    organization_members = models.ManyToManyField('Organization', blank=True)
    election_period_months = models.IntegerField(default=0)
    current_election = models.ForeignKey(
        'PositionElection', models.SET_NULL, blank=True, null=True,
        related_name='+')
    last_election = models.ForeignKey(
        'PositionElection', models.SET_NULL, blank=True, null=True,
        related_name='+')
    heir_first = models.ForeignKey(
        'character.Character', models.SET_NULL, blank=True, null=True,
        related_name='first_heir_to')
    heir_second = models.ForeignKey(
        'character.Character', models.SET_NULL, blank=True, null=True,
        related_name='second_heir_to')
    tax_countdown = models.SmallIntegerField(default=0)

    def has_tax_collection(self):
        return self.violence_monopoly and not self.barbaric

    def remove_member(self, member):
        if member not in self.character_members.all():
            raise Exception("{} is not a member of {}".format(member, self))
        self.character_members.remove(
            member
        )

        if self.leader and member in \
                self.leader.character_members.all():
            self.leader.remove_member(member)

        if member.get_violence_monopoly() is None:
            member.world.get_barbaric_state().character_members.add(
                member
            )

        if self.is_position:
            if (
                    self.heir_first and
                    self.heir_first in self.get_heir_candidates()
            ):
                self.character_members.add(self.heir_first)
                self.heir_first = self.heir_second = None
                self.save()
            elif (
                    self.heir_second and
                    self.heir_second in self.get_heir_candidates()
            ):
                self.character_members.add(self.heir_second)
                self.heir_first = self.heir_second = None
                self.save()
            elif self.position_type == self.ELECTED:
                self.convoke_elections()

        if self.leader and self.leader.character_is_member(member):
            self.leader.remove_member(member)

        message = shortcuts.create_message(
            'messaging/messages/member_left_organization.html',
            self.world,
            'leaving',
            {
                'organization': self,
                'member': member
            },
            link=self.get_absolute_url()
        )
        shortcuts.add_organization_recipient(
            message,
            self,
            add_lead_organizations=True
        )

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

    def organizations_character_can_apply_capabilities_to_this_with(
            self, character, capability_type):
        result = []
        capabilities = capability.Capability.objects.filter(
            applying_to=self, type=capability_type)
        for possible_caps in capabilities:
            if possible_caps.organization.character_can_use_capabilities(
                    character):
                result.append(possible_caps.organization)
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
        return None

    def conquestable_tiles(self):
        if not self.violence_monopoly:
            return None
        candidate_tiles = world.models.geography.Tile.objects \
            .filter(world=self.world) \
            .exclude(controlled_by=self) \
            .exclude(type__in=(world.models.geography.Tile.SHORE,
                               world.models.geography.Tile.DEEPSEA))
        result = []
        for tile in candidate_tiles:
            conquest_tile_event = tile.tileevent_set.filter(
                organization=self,
                type=world.models.events.TileEvent.CONQUEST,
                active=True
            )
            conquering_units = tile.get_units() \
                .filter(owner_character__in=self.character_members.all()) \
                .exclude(status=unit.models.WorldUnit.NOT_MOBILIZED)
            if (
                    conquering_units.exists() and not conquest_tile_event.exists()
            ):
                result.append(tile)
        return result

    def get_open_proposals(self):
        return capability.CapabilityProposal.objects.filter(
            capability__organization=self,
            closed=False
        )

    def get_all_controlled_tiles(self):
        return world.models.geography.Tile.objects.filter(
            controlled_by__in=self.get_descendants_list(including_self=True)
        )

    def external_capabilities_to_this(self):
        return self.capabilities_to_this.exclude(organization=self)

    def get_position_occupier(self):
        if not self.is_position or not self.character_members.exists():
            return None
        return list(self.character_members.all())[0]

    def get_relationship_to(self, target_organization):
        return relationship.OrganizationRelationship.objects.get_or_create(
            defaults={
                'relationship': (relationship.OrganizationRelationship.WAR
                                 if target_organization.barbaric or
                                    self.barbaric else
                                 relationship.OrganizationRelationship.PEACE)
            },
            from_organization=self,
            to_organization=target_organization
        )[0]

    def get_relationship_from(self, organization):
        return organization.get_relationship_to(self)

    def get_default_stance_to(self, state):
        return relationship.MilitaryStance.objects.get_or_create(
            from_organization=self,
            to_organization=state,
            region=None
        )[0]

    def get_region_stances_to(self, state):
        return relationship.MilitaryStance.objects.filter(
            from_organization=self,
            to_organization=state,
        ).exclude(region=None)

    def get_region_stance_to(self, state, region):
        return relationship.MilitaryStance.objects.get_or_create(
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
        new_election = election.PositionElection.objects.create(
            position=self,
            turn=self.world.current_turn + months_to_election
        )
        self.current_election = new_election
        self.save()
        if self.get_position_occupier() is not None:
            election.PositionCandidacy.objects.create(
                election=new_election,
                candidate=self.get_position_occupier(),
                description="Automatic candidacy for incumbent character."
            )

        message = shortcuts.create_message(
            'messaging/messages/elections_convoked.html',
            self.world,
            'elections',
            {'organization': self},
            link=new_election.get_absolute_url()
        )
        shortcuts.add_organization_recipient(
            message,
            self,
            add_lead_organizations=True
        )
        return self.current_election

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            'organization:view',
            kwargs={'organization_id': self.id}
        )

    def get_short_html_name(self):
        return self.get_html_name(include_occupier=False)

    def get_html_name(self, include_occupier=True):
        template = '{name}{icon}{suffix}'
        icon = self.get_bootstrap_icon()

        occupier = self.get_position_occupier()
        if occupier and include_occupier:
            suffix = '<small>{}</small>'.format(occupier.name)
        else:
            suffix = ''

        return format_html(
            template,
            name=self.name,
            icon=mark_safe(icon),
            suffix=mark_safe(suffix)
        )

    def get_bootstrap_icon(self):
        template = '<span style="color: #{color}" ' \
                   'class="glyphicon glyphicon-{icon}" ' \
                   'aria-hidden="true"></span>'
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
        return format_html(template,
                           icon=icon,
                           color=escape(self.color),
                           )

    def get_html_link(self):
        return format_html(
            '<a href="{url}">{name}</a>',
            url=mark_safe(self.get_absolute_url()),
            name=mark_safe(self.get_html_name())
        )

    def current_elections_can_vote_in(self):
        result = []
        elect_capabilities = capability.Capability.objects.filter(
            type=capability.Capability.ELECT,
            organization=self
        )
        for elect_capability in elect_capabilities:
            if elect_capability.applying_to.current_election is not None:
                result.append(elect_capability)
        return result

    def get_heir_candidates(self):
        # TODO this works only for violence monopolies
        return self.get_violence_monopoly(). \
            get_membership_including_descendants()
