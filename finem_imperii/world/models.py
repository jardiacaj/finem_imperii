from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


class Character(models.Model):
    name = models.CharField(max_length=100)
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
    name = models.CharField(max_length=100)
    power = models.IntegerField()

    def __str__(self):
        return self.name
