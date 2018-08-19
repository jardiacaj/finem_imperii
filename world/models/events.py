from django.db import models

import organization.models.organization
from world.models.geography import Tile


class TileEvent(models.Model):
    CONQUEST = 'conquest'
    TYPE_CHOICES = (
        (CONQUEST, CONQUEST),
    )

    tile = models.ForeignKey(Tile, models.CASCADE)
    create_timestamp = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True)
    counter = models.IntegerField(blank=True, null=True,
                                  help_text='Counter for general use')
    start_turn = models.IntegerField()
    end_turn = models.IntegerField(blank=True, null=True)
    organization = models.ForeignKey(
        organization.models.organization.Organization, models.SET_NULL,
        blank=True, null=True)
