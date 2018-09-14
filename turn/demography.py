import random
from multiprocessing.pool import Pool

from django import db
from django.db import transaction
from django.db.models import F

import world.initialization
from parallelism import max_parallelism
from world.models.buildings import Building
from world.models.geography import World, Settlement


def worldwide_population_changes(world: World):
    for tile in world.tile_set.all():
        for settlement in tile.settlement_set.all():
            do_settlement_population_changes(settlement)


def do_settlement_population_changes(settlement: Settlement):
    settlement.update_population()
    amount_to_generate = 0

    if settlement.population < 50:
        amount_to_generate += 5

    if (
            settlement.population < settlement.population_default and
            settlement.get_hunger_percentage() < 3
    ):
        amount_to_generate += int(settlement.population * 0.05)

    residences = settlement.building_set.filter(
        type=Building.RESIDENCE).all()
    for i in range(amount_to_generate):
        world.initialization.generate_npc(i, residences, settlement)
    if amount_to_generate > 0:
        settlement.update_population()


def worldwide_food_consumption(world: World):
    db.connections.close_all()
    p = Pool(max_parallelism())
    p.map(
        do_settlement_food_consumption,
        Settlement.objects.filter(tile__world=world)[:]
    )

@transaction.atomic
def do_settlement_food_consumption(settlement: Settlement):
    mouths = settlement.population
    granary = settlement.get_default_granary()
    bushels_to_consume = min(
        mouths,
        granary.population_consumable_bushels()
    )
    granary.consume_bushels(bushels_to_consume)

    hunger = mouths - bushels_to_consume
    if hunger > 0 and settlement.npc_set.exists():
        for npc in random.sample(
                list(settlement.npc_set.all()),
                min(hunger, settlement.npc_set.count())
        ):
            npc.hunger += 1
            npc.save()

    if hunger == 0 and settlement.npc_set.filter(hunger__gt=0).exists():
        settlement.npc_set.filter(hunger__gt=0).update(
            hunger=F('hunger')-1
        )

    for npc in settlement.npc_set.filter(hunger__gt=3):
        if random.getrandbits(3) == 0:
            npc.take_hit()
        if npc.hunger > 5:
            npc.take_hit()

    settlement.update_population()
