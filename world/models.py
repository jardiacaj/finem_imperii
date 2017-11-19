import math
import random
from collections import namedtuple
from math import sqrt

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models

import organization.models
from battle.models import BattleUnit, BattleSoldierInTurn, BattleCharacter
from character.models import Character
from messaging import shortcuts
from messaging.models import CharacterMessage, MessageRecipient
from unit.models import WorldUnit
from world.templatetags.extra_filters import turn_to_date

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

    def broadcast(self, template, category, context=None, link=None):
        if context is None:
            context = {}

        message = shortcuts.create_message(
            template=template,
            world=self,
            category=category,
            template_context=context,
            link=link,
        )
        for character in self.character_set.all():
            shortcuts.add_character_recipient(message, character)

    def get_violence_monopolies(self):
        return self.organization_set.filter(violence_monopoly=True)

    def get_barbaric_state(self):
        return organization.models.Organization.objects.get(
            world=self,
            barbaric=True
        )

    def __str__(self):
        return self.name

    def get_current_date(self):
        return turn_to_date(self.current_turn)

    def get_html_link(self):
        return '<a href="{}">{}</a>'.format(
            self.get_absolute_url(),
            self.name
        )

    def get_absolute_url(self):
        return reverse('world:world', kwargs={'world_id': self.id})


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
    organization = models.ForeignKey(
        organization.models.Organization, blank=True, null=True)
    counter = models.IntegerField(blank=True, null=True)
    start_turn = models.IntegerField()
    end_turn = models.IntegerField(blank=True, null=True)


settlement_size_names = [
    (lambda x: x < 10, "dwelling"),
    (lambda x: x < 100, "hamlet"),
    (lambda x: x < 1000, "village"),
    (lambda x: x < 5000, "town"),
    (lambda x: x < 10000, "large town"),
    (lambda x: x < 50000, "city"),
    (lambda x: x < 200000, "large city"),
    (lambda x: True, "metropolis"),
]


class Settlement(models.Model):
    GUILDS_PROHIBIT = 'prohibit guilds'
    GUILDS_RESTRICT = 'restrict guilds'
    GUILDS_KEEP = 'keep guilds'
    GUILDS_PROMOTE = 'promote guilds'
    GUILDS_CHOICES = (
        (GUILDS_PROHIBIT, GUILDS_PROHIBIT),
        (GUILDS_RESTRICT, GUILDS_RESTRICT),
        (GUILDS_KEEP, GUILDS_KEEP),
        (GUILDS_PROMOTE, GUILDS_PROMOTE),
    )

    name = models.CharField(max_length=100)
    tile = models.ForeignKey(Tile)
    population = models.IntegerField(default=0)
    population_default = models.IntegerField()
    x_pos = models.IntegerField()
    z_pos = models.IntegerField()
    public_order = models.IntegerField(
        default=1000, help_text="0-1000, shown as %")
    guilds_setting = models.CharField(
        max_length=20, default=GUILDS_KEEP, choices=GUILDS_CHOICES)

    def make_public_order_in_range(self):
        self.public_order = min(1000, max(self.public_order, 0))

    def get_public_order_display(self):
        return "{}%".format(self.public_order // 10)

    def size_name(self):
        for size in settlement_size_names:
            if size[0](self.population):
                return size[1]

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
        self.population = self.get_residents().count()
        self.save()

    def get_residents(self):
        return NPC.objects.filter(residence__settlement=self)

    def get_default_granary(self):
        return self.building_set.get(
            type=Building.GRANARY,
            owner=None
        )

    def get_hunger_percentage(self):
        try:
            return round(
                (
                    self.get_residents().filter(hunger__gt=1).count() /
                    self.get_residents().count()
                ) * 100
            )
        except ZeroDivisionError:
            return 0

    def disability_percentage(self):
        try:
            return int(
                self.get_residents().filter(able=False).count() /
                self.get_residents().count()
                * 100
            )
        except ZeroDivisionError:
            return 0

    def female_percentage(self):
        try:
            return int(
                self.get_residents().filter(male=False).count() /
                self.get_residents().count()
                * 100
            )
        except ZeroDivisionError:
            return 0

    def male_percentage(self):
        try:
            return int(
                self.get_residents().filter(male=True).count() /
                self.get_residents().count()
                * 100
            )
        except ZeroDivisionError:
            return 0


class NotEnoughBushels(Exception):
    pass


class Building(models.Model):
    GRAIN_FIELD = 'grain field'
    RESIDENCE = 'residence'
    GRANARY = 'granary'
    GUILD = 'guild'
    PRISON = 'prison'

    TYPE_CHOICES = (
        (GRAIN_FIELD, GRAIN_FIELD),
        (RESIDENCE, RESIDENCE),
        (GRANARY, GRANARY),
        (PRISON, PRISON),
        (GUILD, GUILD),
    )

    LEVEL_DESCRIPTORS = {
        GRAIN_FIELD:
            [
                ('barren land', '{qty} barren lands'),
                ('open field', '{qty} open fields'),
                ('fenced field', '{qty} fenced fields'),
            ],
        RESIDENCE:
            [
                ('shack', '{qty} shacks'),
                ('low quality house', '{qty} low quality houses'),
                ('simple house', '{qty} simple houses'),
            ],
        GRANARY:
            [
                ('open heap', '{} open heaps'),
                ('basic granary', '{} basic granaries'),
                ('proper granary', '{} proper granaries'),
            ],
        PRISON:
            [
                ('prisoner cage', '{} prisoner cages'),
                ('jail', '{} jails'),
                ('simple prison', '{} simple prisons'),
            ],
        GUILD:
            [
                ('informal guild', '{} informal guilds'),
                ('organized guild', '{} organized guilds'),
                ('guild confraternity', '{} guild confraternity'),
            ],
    }

    level = models.SmallIntegerField(default=1, help_text="Go from 1 to 5")
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    quantity = models.IntegerField(default=1)
    settlement = models.ForeignKey(Settlement)
    field_production_counter = models.IntegerField(default=0)
    owner = models.ForeignKey(
        'organization.Organization', null=True, blank=True,
        help_text="NULL means 'owned by local population'"
    )

    def worker_percent(self):
        return int(
            self.worker.count() / self.max_ideal_workers() * 100
        )

    def max_workers(self):
        if self.type == self.GUILD:
            return self.quantity * 20000
        elif self.type == self.GRAIN_FIELD:
            return math.floor(self.quantity / 2)
        else:
            return 0

    def max_ideal_workers(self):
        if self.type == self.GUILD:
            return self.quantity * 10000
        elif self.type == self.GRAIN_FIELD:
            return math.ceil(self.quantity / 10)
        else:
            return 0

    def max_surplus_workers(self):
        return self.max_workers() - self.max_ideal_workers()

    def add_bushels(self, bushels_to_add):
        bushel_object = self.get_public_bushels_object()
        bushel_object.quantity += bushels_to_add
        bushel_object.save()

    def consume_bushels(self, bushels_to_consume):
        bushel_object = self.get_public_bushels_object()
        if bushels_to_consume > bushel_object.quantity:
            raise NotEnoughBushels()
        bushel_object.quantity -= bushels_to_consume
        bushel_object.save()

    def get_public_bushels_object(self):
        if not self.type == self.GRANARY:
            return
        return InventoryItem.objects.get_or_create(
            type=InventoryItem.GRAIN,
            owner_character=None,
            location=self,
            defaults={'quantity': 0}
        )[0]

    def population_consumable_bushels(self):
        bushel_object = self.get_public_bushels_object()
        return bushel_object.quantity

    def grain_reserve_in_months(self):
        try:
            return math.floor(
                self.population_consumable_bushels() /
                self.settlement.population
            )
        except ZeroDivisionError:
            return 0

    def __str__(self):
        return self.LEVEL_DESCRIPTORS[self.type][self.level][
            0 if self.quantity == 1 else 1
        ].format(qty=self.quantity)


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
        index_together = (
            ('residence', 'hunger')
        )
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
        'unit.WorldUnit', null=True, blank=True, related_name='soldier'
    )
    trained_soldier = models.BooleanField(default=None)
    skill_fighting = models.IntegerField()
    wound_status = models.SmallIntegerField(
        choices=BattleSoldierInTurn.WOUND_STATUS_CHOICES,
        default=BattleSoldierInTurn.UNINJURED
    )
    hunger = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    def take_hit(self):
        if self.wound_status == BattleSoldierInTurn.DEAD:
            return
        self.wound_status += 1
        self.save()
        if self.wound_status == BattleSoldierInTurn.DEAD:
            self.die()
        self.ability_roll()

    def ability_roll(self):
        if self.wound_status == BattleSoldierInTurn.MEDIUM_WOUND:
            if random.getrandbits(3) == 0:
                self.able = False
                self.save()
        if self.wound_status == BattleSoldierInTurn.HEAVY_WOUND:
            if random.getrandbits(1) == 0:
                self.able = False
                self.save()

    def die(self):
        unit = self.unit
        self.location = None
        self.residence = None
        self.unit = None
        self.able = False
        self.save()

        if unit and unit.soldier.count() == 0:
            unit.disband()


class InventoryItem(models.Model):
    GRAIN = 'grain'
    CART = 'cart'
    TYPE_CHOICES = (
        (GRAIN, 'grain bushels'),
        (CART, 'transport carts'),
    )

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField(default=1)
    owner_character = models.ForeignKey(Character, blank=True, null=True)
    location = models.ForeignKey(Building, blank=True, null=True)

    def __str__(self):
        return "{} {}".format(self.quantity, self.get_type_display())

    def get_weight(self):
        if self.type == InventoryItem.CART:
            return -100
        return 1
