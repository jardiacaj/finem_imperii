import random

from unit.models import WorldUnit
from world.models.geography import World, Settlement


def worldwide_public_order(world: World):
    for tile in world.tile_set.all():
        for settlement in tile.settlement_set.all():
            do_settlement_public_order_update(settlement)


def do_settlement_public_order_update(settlement: Settlement):
    hunger_percent = settlement.get_hunger_percentage()
    if hunger_percent > 20:
        settlement.public_order -= (hunger_percent - 20) * 5
    elif hunger_percent < 10:
        settlement.public_order += (10 - hunger_percent) * 10
    settlement.make_public_order_in_range()

    non_barbarian_units = WorldUnit.objects.filter(
        location=settlement,
        owner_character__isnull=False
    )

    public_order_contributing_units = []
    settlement_vm = settlement.tile.controlled_by.get_violence_monopoly()
    for non_barbarian_unit in non_barbarian_units:
        char_vm = non_barbarian_unit.owner_character.get_violence_monopoly()
        if char_vm == settlement_vm:
            public_order_contributing_units.append(
                non_barbarian_unit
            )
    contributing_soldiers = sum(
        [unit.soldier.count() for unit in public_order_contributing_units]
    )
    soldier_to_pop_ratio = contributing_soldiers / settlement.population

    settlement.public_order += soldier_to_pop_ratio * 500
    settlement.make_public_order_in_range()

    if soldier_to_pop_ratio < 0.05:
        settlement.public_order -= random.randint(0, 70)

    settlement.make_public_order_in_range()
    settlement.save()
