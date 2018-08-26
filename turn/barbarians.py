import random

import unit.models
import unit.creation
from world.models.geography import World, Settlement


def worldwide_barbarian_generation(world: World):
    world_settlements = Settlement.objects.filter(
        tile__world=world
    )
    for settlement in world_settlements:
        do_settlement_barbarian_generation(settlement)


def do_settlement_barbarian_generation(settlement: Settlement):
    if settlement.population < 40:
        return

    pure_barbarian_units = unit.models.WorldUnit.objects.filter(
        location=settlement,
        owner_character__isnull=True
    )
    barbarian_soldiers = sum(
        [unit.soldier.count() for unit in pure_barbarian_units]
    )

    non_barbarian_units = unit.models.WorldUnit.objects.filter(
        location=settlement,
        owner_character__isnull=False
    )
    non_barbarian_soldiers = sum(
        [unit.soldier.count() for unit in non_barbarian_units]
    )

    if settlement.tile.controlled_by.get_violence_monopoly().barbaric:
        if (
                barbarian_soldiers < settlement.population * 0.2
                and non_barbarian_soldiers < settlement.population * 0.2
        ):
            recruitment_size = random.randrange(
                int(settlement.population * 0.05),
                int(settlement.population * 0.15)
            )
            generate_barbarian_unit(recruitment_size, settlement)

    else:
        if settlement.public_order < 500:
            public_order_ratio = settlement.public_order / 1000
            public_disorder_ratio = 1 - public_order_ratio

            if barbarian_soldiers >= \
                            settlement.population * public_disorder_ratio:
                return
            recruitment_size = random.randrange(10, settlement.population // 3)
            generate_barbarian_unit(recruitment_size, settlement)


def generate_barbarian_unit(recruitment_size, settlement):
    soldiers = unit.creation.sample_candidates(
        unit.creation.all_recruitable_soldiers_in_settlement(settlement),
        recruitment_size
    )
    unit.creation.create_unit(
        "Barbarians of {}".format(settlement),
        None,
        settlement,
        soldiers,
        unit.models.WorldUnit.CONSCRIPTED,
        unit.models.WorldUnit.LIGHT_INFANTRY
    )
