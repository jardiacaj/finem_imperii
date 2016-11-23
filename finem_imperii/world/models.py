from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from django.forms.models import model_to_dict


class World(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('world:world', kwargs={'world_id': self.id})


class Tile(models.Model):
    name = models.CharField(max_length=100)
    world = models.ForeignKey(World)
    x_pos = models.IntegerField()
    y_pos = models.FloatField()
    z_pos = models.IntegerField()
    type = models.CharField(max_length=15)

    def __str__(self):
        return self.name

    def render_for_view(self):
        return model_to_dict(self)


class Character(models.Model):
    name = models.CharField(max_length=100)
    world = models.ForeignKey(World)
    region = models.ForeignKey(Tile)
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
    power = models.IntegerField()

    def __str__(self):
        return self.name
