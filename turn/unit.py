from unit.models import WorldUnit
from world.models.geography import World


def worldwide_unit_maintenance(world: World):
    for unit in world.worldunit_set.all():
        do_unit_status_update(unit)
        do_unit_debt_increase(unit)
        if unit.auto_pay and unit.owner_character:
            if unit.get_owners_debt() <= unit.owner_character.cash:
                unit.pay_debt(unit.owner_character)


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
        for soldier in unit.soldier.all():
            soldier.unit_debt += 1
            soldier.save()
