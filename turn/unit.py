from unit.models import WorldUnit
from world.models.geography import World


def worldwide_unit_maintenance(world: World):
    for unit in world.worldunit_set.all():
        do_unit_status_update(unit)
        do_unit_debt_increase(unit)


def do_unit_status_update(unit: WorldUnit):
    if unit.status == WorldUnit.REGROUPING:
        if (
            unit.owner_character is not None and
            unit.location == unit.owner_character.location
        ):
            unit.status = WorldUnit.FOLLOWING
        else:
            unit.status = WorldUnit.STANDING
        unit.save()


def do_unit_debt_increase(unit: WorldUnit):
    if unit.owner_character and unit.status != WorldUnit.NOT_MOBILIZED:
        unit.owners_debt += unit.monthly_cost()
