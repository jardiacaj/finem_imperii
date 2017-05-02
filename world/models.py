import random

import math
from collections import namedtuple
from math import sqrt

from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models.aggregates import Avg

from battle.models import BattleUnit
from messaging.models import CharacterMessage, MessageRecipient
from organization.models import Organization
from world.templatetags.extra_filters import nice_hours
from world.turn import TurnProcessor, turn_to_date, organizations_with_battle_ready_units, \
    opponents_in_organization_list, get_largest_conflict_in_list, create_battle_from_conflict

Point = namedtuple('Point', ['x', 'z'])


def euclidean_distance(p1, p2):
    return sqrt((p1.x - p2.x)**2 + (p1.z - p2.z)**2)


class World(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    initialized = models.BooleanField(default=False)
    current_turn = models.IntegerField(default=0)
    blocked_for_turn = models.BooleanField(
        default=False, help_text="True during turn processing"
    )

    def get_violence_monopolies(self):
        return self.organization_set.filter(violence_monopoly=True)

    def __str__(self):
        return self.name

    def get_current_date(self):
        return turn_to_date(self.current_turn)

    def get_absolute_url(self):
        return reverse('world:world', kwargs={'world_id': self.id})

    def pass_turn(self):
        self.blocked_for_turn = True
        self.save()
        turn_processor = TurnProcessor(self)
        turn_processor.do_turn()
        self.blocked_for_turn = False
        self.save()


class Region(models.Model):
    class Meta:
        unique_together = (
            ("world", "name"),
        )

    name = models.CharField(max_length=100)
    world = models.ForeignKey(World)

    def __str__(self):
        return self.name


class Tile(models.Model):
    PLAINS = 'plains'
    FOREST = 'forest'
    SHORE = 'shore'
    DEEPSEA = 'deepsea'
    MOUNTAIN = 'mountain'
    TYPE_CHOICES = (
        (PLAINS, PLAINS),
        (FOREST, FOREST),
        (SHORE, SHORE),
        (DEEPSEA, "deep sea"),
        (MOUNTAIN, MOUNTAIN),
    )

    class Meta:
        unique_together = (
            ("world", "x_pos", "z_pos"),
        )

    name = models.CharField(max_length=100)
    world = models.ForeignKey(World)
    region = models.ForeignKey(Region)
    controlled_by = models.ForeignKey('organization.Organization')
    x_pos = models.IntegerField()
    y_pos = models.FloatField()
    z_pos = models.IntegerField()
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('world:tile', kwargs={'tile_id': self.id})

    def get_html_link(self):
        return '<a href="{url}">{name}</a>'.format(
            url=self.get_absolute_url(), name=self.name
        )

    def get_absolute_coords(self):
        return Point(x=self.x_pos, z=self.z_pos)

    def distance_to(self, tile):
        if self.world != tile.world:
            raise Exception("Can't calculate distance between worlds")
        return euclidean_distance(
            self.get_absolute_coords(), tile.get_absolute_coords()
        )

    def is_on_ground(self):
        return self.type in (Tile.PLAINS, Tile.FOREST, Tile.MOUNTAIN)

    def get_units(self):
        return WorldUnit.objects.filter(location__tile=self)

    def trigger_battles(self):
        conflicts = opponents_in_organization_list(
            organizations_with_battle_ready_units(self),
            self
        )
        conflict = get_largest_conflict_in_list(conflicts, self)
        if conflict:
            return create_battle_from_conflict(conflict, self)

    def get_current_battles(self):
        return self.battle_set.filter(current=True)

    def get_total_population(self):
        return sum(
            settlement.population for settlement in self.settlement_set.all()
        )


class TileEvent(models.Model):
    CONQUEST = 'conquest'
    TYPE_CHOICES = (
        (CONQUEST, CONQUEST),
    )

    tile = models.ForeignKey(Tile)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True)
    organization = models.ForeignKey(Organization, blank=True, null=True)
    counter = models.IntegerField(blank=True, null=True)
    start_turn = models.IntegerField()
    end_turn = models.IntegerField(blank=True, null=True)


class Settlement(models.Model):
    name = models.CharField(max_length=100)
    tile = models.ForeignKey(Tile)
    population = models.IntegerField()
    x_pos = models.IntegerField()
    z_pos = models.IntegerField()

    def size_name(self):
        if self.population < 10:
            return "dwelling"
        if self.population < 100:
            return "hamlet"
        if self.population < 1000:
            return "village"
        if self.population < 5000:
            return "town"
        if self.population < 10000:
            return "large town"
        if self.population < 50000:
            return "city"
        if self.population < 200000:
            return "large city"
        return "metropolis"

    def __str__(self):
        return self.name

    def base_conscription_cost(self):
        return math.ceil(math.log10(self.population) * 12)

    def conscription_time(self, soldiers):
        return math.ceil(self.base_conscription_cost() + soldiers / 5)

    def get_absolute_coords(self):
        return Point(
            x=self.tile.x_pos * 100 + self.x_pos,
            z=self.tile.z_pos * 100 + self.z_pos,
        )

    def distance_to(self, settlement):
        if self.tile.world != settlement.tile.world:
            raise Exception("Can't calculate distance between worlds")
        return euclidean_distance(
            self.get_absolute_coords(),
            settlement.get_absolute_coords()
        )

    def update_population(self):
        self.population = self.npc_set.all().count()
        self.save()


class Building(models.Model):
    GRAIN_FIELD = 'grain field'
    RESIDENCE = 'residence'
    SAWMILL = 'sawmill'
    IRON_MINE = 'iron mine'
    GRANARY = 'granary'
    PRISON = 'prison'

    TYPE_CHOICES = (
        (GRAIN_FIELD, GRAIN_FIELD),
        (RESIDENCE, RESIDENCE),
        (SAWMILL, SAWMILL),
        (IRON_MINE, IRON_MINE),
        (GRANARY, GRANARY),
        (PRISON, PRISON),
    )

    level = models.SmallIntegerField(default=1, help_text="Go from 1 to 5")
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    quantity = models.IntegerField(default=1)
    settlement = models.ForeignKey(Settlement)
    owner = models.ForeignKey(
        'organization.Organization', null=True, blank=True,
        help_text="NULL means 'owned by local population'"
    )

    def max_employment(self):
        if self.type:
            return math.ceil(self.quantity / 2)


class NPCManager(models.Manager):
    def gender_distribution(self):
        return {
            'female': self.get_queryset().filter(male=False).count(),
            'male': self.get_queryset().filter(male=True).count()
        }

    def skill_distribution(self):
        return {
            'high skill': self.get_queryset().filter(
                skill_fighting__gte=NPC.TOP_SKILL_LIMIT
            ).count(),
            'medium skill': self.get_queryset().filter(
                skill_fighting__gte=NPC.MEDIUM_SKILL_LIMIT,
                skill_fighting__lt=NPC.TOP_SKILL_LIMIT
            ).count(),
            'low skill': self.get_queryset().filter(
                skill_fighting__lt=NPC.MEDIUM_SKILL_LIMIT
            ).count(),
        }

    def age_distribution(self):
        return {
            'too young': self.get_queryset().filter(
                age_months__lt=NPC.VERY_YOUNG_AGE_LIMIT
            ).count(),
            'very young': self.get_queryset().filter(
                age_months__gte=NPC.VERY_YOUNG_AGE_LIMIT,
                age_months__lt=NPC.YOUNG_AGE_LIMIT
            ).count(),
            'young': self.get_queryset().filter(
                age_months__gte=NPC.YOUNG_AGE_LIMIT,
                age_months__lt=NPC.MIDDLE_AGE_LIMIT
            ).count(),
            'middle age': self.get_queryset().filter(
                age_months__gte=NPC.MIDDLE_AGE_LIMIT,
                age_months__lt=NPC.OLD_AGE_LIMIT
            ).count(),
            'old': self.get_queryset().filter(
                age_months__gte=NPC.OLD_AGE_LIMIT
            ).count(),
        }

    def professionality_distribution(self):
        return {
            'professional':
                self.get_queryset().filter(trained_soldier=True).count(),
            'non-professional':
                self.get_queryset().filter(trained_soldier=False).count()
        }

    def origin_distribution(self):
        result = {}
        for npc in self.get_queryset().all():
            result[npc.origin.name] = result.get(npc.origin.name, 0) + 1
        return result


class NPC(models.Model):
    class Meta:
        base_manager_name = 'stats_manager'
    stats_manager = NPCManager()
    objects = models.Manager()

    TOP_SKILL_LIMIT = 70
    MEDIUM_SKILL_LIMIT = 35

    OLD_AGE_LIMIT = 50*12
    MIDDLE_AGE_LIMIT = 35*12
    YOUNG_AGE_LIMIT = 18*12
    VERY_YOUNG_AGE_LIMIT = 12*12

    name = models.CharField(max_length=100)
    male = models.BooleanField()
    able = models.BooleanField()
    age_months = models.IntegerField()
    origin = models.ForeignKey(Settlement, related_name='offspring')
    residence = models.ForeignKey(
        Building, null=True, blank=True, related_name='resident'
    )
    location = models.ForeignKey(Settlement, null=True, blank=True)
    workplace = models.ForeignKey(
        Building, null=True, blank=True, related_name='worker'
    )
    unit = models.ForeignKey(
        'WorldUnit', null=True, blank=True, related_name='soldier'
    )
    trained_soldier = models.BooleanField(default=None)
    skill_fighting = models.IntegerField()

    def __str__(self):
        return self.name


class Character(models.Model):
    name = models.CharField(max_length=100)
    world = models.ForeignKey(World)
    location = models.ForeignKey(Settlement)
    oath_sworn_to = models.ForeignKey(
        'organization.Organization', null=True, blank=True
    )
    owner_user = models.ForeignKey(User)
    cash = models.IntegerField(default=0)
    hours_in_turn_left = models.IntegerField(default=15*24)
    travel_destination = models.ForeignKey(
        Settlement, null=True, blank=True, related_name='travellers_heading'
    )

    @property
    def activation_url(self):
        return reverse('world:activate_character', kwargs={'char_id': self.id})

    def travel_time(self, target_settlement):
        distance = self.location.distance_to(target_settlement)
        if (self.location.tile.type == Tile.MOUNTAIN
                or target_settlement.tile.type == Tile.MOUNTAIN):
            distance *= 2
        days = distance / 100 * 2
        return math.ceil(days * 24)

    def check_travelability(self, target_settlement):
        if target_settlement == self.location:
            return "You can't travel to {} as you are already there.".format(
                target_settlement
            )
        if target_settlement.tile.distance_to(self.location.tile) > 1.5:
            return "You can only travel to contiguous regions."
        if (self.travel_destination is not None
                and self.travel_destination != target_settlement):
            return "You cant travel to {} because you are already travelling" \
                   " to {}.".format(
                        target_settlement,
                        self.travel_destination
                   )
        return None

    def perform_travel(self, destination):
        travel_time = self.travel_time(destination)
        self.location = destination
        self.hours_in_turn_left -= travel_time
        self.save()
        return "After {} of travel you have reached {}.".format(
            nice_hours(travel_time), destination
        )

    @transaction.atomic
    def add_notification(self, category, content, safe=False):
        message = CharacterMessage.objects.create(
            content=content,
            category=category,
            creation_turn=self.world.current_turn,
            safe=safe
        )
        MessageRecipient.objects.create(
            message=message,
            character=self
        )

    def get_violence_monopoly(self):
        try:
            return self.organization_set.get(violence_monopoly=True)
        except (Organization.DoesNotExist,
                Organization.MultipleObjectsReturned):
            return None

    def unread_messages(self):
        return CharacterMessage.objects.filter(
            messagerecipient__character=self, messagerecipient__read=False
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('world:character', kwargs={'character_id': self.id})

    def get_html_name(self):
        result = self.name
        for membership in self.organization_set.all():
            result += membership.get_bootstrap_icon()
        return result

    def get_html_link(self):
        return '<a href="{}">{}</a>'.format(
            self.get_absolute_url(), self.get_html_name()
        )


class WorldUnitStatusChangeException(Exception):
    pass


class WorldUnit(models.Model):
    CONSCRIPTION = 'conscription'
    PROFESSIONAL = 'professional'
    MERCENARY = 'mercenary'
    RECTRUITMENT_CHOICES = (
        (CONSCRIPTION, CONSCRIPTION),
        (PROFESSIONAL, PROFESSIONAL),
        (MERCENARY, MERCENARY),
    )

    INFANTRY = 'infantry'
    PIKEMEN = 'pikemen'
    ARCHERS = 'archers'
    CAVALRY = 'cavalry'
    CATAPULT = 'catapult'
    SIEGE_TOWER = 'siege tower'
    RAM = 'ram'
    TYPE_CHOICES = (
        (INFANTRY, INFANTRY),
        (PIKEMEN, PIKEMEN),
        (ARCHERS, ARCHERS),
        (CAVALRY, CAVALRY),
        (CATAPULT, CATAPULT),
        (SIEGE_TOWER, SIEGE_TOWER),
        (RAM, RAM),
    )

    NOT_MOBILIZED = 'not mobilized'
    TRAINING = 'training'
    STANDING = 'standing'
    FOLLOWING = 'following'
    CUSTOMER_SEARCH = 'customer search'
    STATUS_CHOICES = (
        (NOT_MOBILIZED, NOT_MOBILIZED),
        (TRAINING, TRAINING),
        (STANDING, STANDING),
        (FOLLOWING, FOLLOWING),
        (CUSTOMER_SEARCH, CUSTOMER_SEARCH),
    )

    LINE_CHOICES = (
        (0, "Advanced line"),
        (1, "Front line"),
        (2, "Middle line"),
        (3, "Rear line"),
        (4, "Rearguard"),
    )

    SIDE_CHOICES = (
        (-5, "Flanking far left"),
        (-4, "Flanking left"),
        (-3, "Cover left flank"),
        (-2, "Left side"),
        (-1, "Left-center"),
        (0, "Center"),
        (1, "Right-center"),
        (2, "Right side"),
        (3, "Cover right flank"),
        (4, "Flanking right"),
        (5, "Flanking far right"),
    )

    owner_character = models.ForeignKey(Character, blank=True, null=True)
    world = models.ForeignKey(World)
    location = models.ForeignKey(Settlement)
    name = models.CharField(max_length=100)
    recruitment_type = models.CharField(
        max_length=30, choices=RECTRUITMENT_CHOICES
    )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    mobilization_status_since = models.IntegerField()
    current_status_since = models.IntegerField()
    battle_line = models.IntegerField(choices=LINE_CHOICES, default=3)
    battle_side_pos = models.IntegerField(choices=SIDE_CHOICES, default=0)
    generation_size = models.IntegerField(
        default=0, help_text="Only used in tests that need generated units"
    )
    default_battle_orders = models.ForeignKey('battle.Order')

    @staticmethod
    def get_unit_types(nice=False):
        return (unit_type[1 if nice else 0]
                for unit_type in WorldUnit.TYPE_CHOICES)

    @staticmethod
    def get_unit_states(nice=False):
        return (state[1 if nice else 0] for state in WorldUnit.STATUS_CHOICES)

    def __str__(self):
        return self.name

    def descriptor(self):
        return "{} {}".format(self.soldier.count(), self.type.capitalize())

    def get_absolute_url(self):
        return reverse('world:unit', kwargs={'unit_id': self.id})

    def average_fighting_skill(self):
        return round(
            self.soldier.all().aggregate(
                Avg('skill_fighting')
            )['skill_fighting__avg']
        )

    def change_status(self, new_status):
        if new_status not in WorldUnit.get_unit_states():
            raise Exception("Invalid unit status {}".format(new_status))
        if self.status == WorldUnit.CUSTOMER_SEARCH:
            raise Exception("Mercenaries can't change_status()")
        if new_status == WorldUnit.CUSTOMER_SEARCH:
            raise Exception("Can't switch to searching customer status")
        if self.get_current_battle() is not None:
            raise WorldUnitStatusChangeException(
                "Can't change status while in battle"
            )
        if self.status == new_status:
            raise WorldUnitStatusChangeException(
                "The unit is already {}".format(self.get_status_display())
            )
        if new_status == WorldUnit.NOT_MOBILIZED:
            if self.mobilization_status_since == self.world.current_turn:
                raise WorldUnitStatusChangeException(
                    "Cannot demobilize {} the same turn it has been"
                    " mobilized".format(self)
                )
        if (new_status != WorldUnit.NOT_MOBILIZED
                and self.status == WorldUnit.NOT_MOBILIZED):
            if self.mobilization_status_since == self.world.current_turn:
                raise WorldUnitStatusChangeException(
                    "Cannot mobilize {} the same turn it has been"
                    " demobilized".format(self)
                )
        if (new_status == WorldUnit.FOLLOWING
                and self.owner_character.location != self.location):
            raise WorldUnitStatusChangeException(
                "A unit can only follow you if you are in the same location."
            )
        self.status = new_status
        self.save()

    def get_fighting_soldiers(self):
        return self.soldier.filter(able=True)

    def get_current_battle(self):
        try:
            in_battle = BattleUnit.objects.get(
                world_unit=self, battle_side__battle__current=True
            )
            return in_battle.battle_side.battle
        except BattleUnit.DoesNotExist:
            pass
