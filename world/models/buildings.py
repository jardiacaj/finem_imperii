import math

from django.db import models

import world.models.items
import world.models.geography


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
                ('low production field', '{qty} low production fields'),
                ('regular field', '{qty} regular fields'),
                ('fertile field', '{qty} fertile fields'),
            ],
        RESIDENCE:
            [
                ('shack', '{qty} shacks'),
                ('shabby house', '{qty} shabby houses'),
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
    settlement = models.ForeignKey('world.Settlement', models.CASCADE)
    field_production_counter = models.IntegerField(default=0)
    owner = models.ForeignKey(
        'organization.Organization', models.SET_NULL, null=True, blank=True,
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
        return world.models.items.InventoryItem.objects.get_or_create(
            type=world.models.items.InventoryItem.GRAIN,
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
