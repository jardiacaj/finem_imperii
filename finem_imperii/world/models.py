from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from django.forms.models import model_to_dict


class World(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    initialized = models.BooleanField(default=False)
    current_turn = models.IntegerField(default=0)

    def get_violence_monopolies(self):
        return self.organization_set.filter(violence_monopoly=True)

    def __str__(self):
        return self.name

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
    controlled_by = models.ForeignKey('organization.Organization', null=True, blank=True)
    x_pos = models.IntegerField()
    y_pos = models.FloatField()
    z_pos = models.IntegerField()
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)

    def __str__(self):
        return self.name

    def render_for_view(self):
        result = model_to_dict(self)
        result['settlements'] = [settlement.render_for_view() for settlement in self.settlement_set.all()]
        return result


class Settlement(models.Model):
    name = models.CharField(max_length=100)
    tile = models.ForeignKey(Tile)
    population = models.IntegerField()
    x_pos = models.IntegerField()
    z_pos = models.IntegerField()

    def render_for_view(self):
        return model_to_dict(self)


class Building(models.Model):
    RESIDENCE = 'residence'
    SAWMILL = 'sawmill'
    IRON_MINE = 'iron mine'
    GRANARY = 'granary'
    PRISON = 'prison'

    TYPE_CHOICES = (
        (RESIDENCE, RESIDENCE),
        (SAWMILL, SAWMILL),
        (IRON_MINE, IRON_MINE),
        (PRISON, PRISON),
    )

    level = models.SmallIntegerField(default=1)
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    quantity = models.IntegerField(default=1)
    settlement = models.ForeignKey(Settlement)
    owner = models.ForeignKey('organization.Organization', null=True, blank=True)


class NPC(models.Model):
    male = models.BooleanField()
    age_months = models.IntegerField()
    residence = models.ForeignKey(Building, null=True, blank=True, related_name='resident')
    location = models.ForeignKey(Settlement, null=True, blank=True)
    workplace = models.ForeignKey(Building, null=True, blank=True, related_name='worker')
    unit = models.ForeignKey('WorldUnit', null=True, blank=True, related_name='soldier')


class Character(models.Model):
    name = models.CharField(max_length=100)
    world = models.ForeignKey(World)
    location = models.ForeignKey(Settlement)
    oath_sworn_to = models.ForeignKey('organization.Organization', null=True, blank=True)
    owner_user = models.ForeignKey(User)
    cash = models.IntegerField(default=0)

    # def get_absolute_url(self):
    #    return reverse('users:profile', args=[str(self.steam_id)])

    @property
    def activation_url(self):
        return reverse('world:activate_character', kwargs={'char_id': self.id})

    def __str__(self):
        return self.name


class WorldUnit(models.Model):
    owner_character = models.ForeignKey(Character)
    world = models.ForeignKey(World)
    region = models.ForeignKey(Tile)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
