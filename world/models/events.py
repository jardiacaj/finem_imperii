from django.db import models

import organization.models
from world.models.geography import Tile


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