import math
from collections import namedtuple
from math import sqrt

from django.db import models
from django.urls import reverse

import organization.models
import unit.models
import world.models.buildings
import world.models.npcs
from messaging import shortcuts
from world.templatetags.extra_filters import turn_to_date

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
        return unit.models.WorldUnit.objects.filter(location__tile=self)

    def get_current_battles(self):
        return self.battle_set.filter(current=True)

    def get_total_population(self):
        return sum(
            settlement.population for settlement in self.settlement_set.all()
        )


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
        return world.models.npcs.NPC.objects.filter(residence__settlement=self)

    def get_default_granary(self):
        return self.building_set.get(
            type=world.models.buildings.Building.GRANARY,
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
