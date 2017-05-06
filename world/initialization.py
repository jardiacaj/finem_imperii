import logging
import random

from django.db import transaction

from name_generator.name_generator import generate_name
from organization.models import Organization
from world.models import Building, NPC
from world.turn import do_settlement_barbarians


class AlreadyInitializedException(Exception):
    pass


@transaction.atomic
def initialize_world(world):
    logging.info("Initializing world {}".format(world))
    if world.initialized:
        raise AlreadyInitializedException("World {} already initialized!".format(world))
    for organization in world.organization_set.all():
        initialize_organization(organization)
    for unit in world.worldunit_set.all():
        initialize_unit(unit)
    for tile in world.tile_set.all():
        initialize_tile(tile)
    world.initialized = True
    world.save()


def initialize_organization(organization):
    if organization.position_type == Organization.ELECTED and organization.get_position_occupier() is None:
        organization.convoke_elections()


def initialize_tile(tile):
    logging.info("Initializing tile {}".format(tile))
    for settlement in tile.settlement_set.all():
        initialize_settlement(settlement)


def initialize_settlement(settlement):
    logging.info("Initializing settlement {}".format(settlement))
    residences = settlement.building_set.filter(type=Building.RESIDENCE).all()
    fields = settlement.building_set.filter(type=Building.GRAIN_FIELD).all()
    total_field_workplaces = sum(field.max_workers() for field in fields)
    other_workplaces = settlement.building_set.exclude(type__in=(Building.RESIDENCE, Building.GRAIN_FIELD)).all()
    total_other_workplaces = sum(j.max_workers() for j in other_workplaces)

    assigned_workers = 0

    for i in range(settlement.population):
        male = random.getrandbits(1)
        name = generate_name(male)

        over_sixty = (random.getrandbits(4) == 0)
        if over_sixty:
            age_months = random.randint(60 * 12, 90 * 12)
            able = random.getrandbits(1)
        else:
            age_months = random.randint(0, 60 * 12)
            able = (random.getrandbits(7) != 0)

        if able:
            assigned_workers += 1

            # we assign 75% of population to fields
            if assigned_workers < settlement.population / 4 or total_other_workplaces == 0:
                # we do a weighted assignment
                pos = random.randint(0, total_field_workplaces)
                cumulative = 0
                for field in fields:
                    cumulative += field.max_workers()
                    if pos < cumulative:
                        break
                workplace = field
            else:
                pos = random.randint(0, total_other_workplaces)
                cumulative = 0
                for other_workplace in other_workplaces:
                    cumulative += other_workplace.max_workers()
                    if pos < cumulative:
                        break
                workplace = other_workplace

        NPC.objects.create(
            name=name,
            male=male,
            able=able,
            age_months=age_months,
            residence=residences[i % residences.count()],
            origin=settlement,
            location=settlement,
            workplace=workplace if able else None,
            unit=None,
            trained_soldier=(random.getrandbits(4) == 0) if age_months >= NPC.VERY_YOUNG_AGE_LIMIT else False,
            skill_fighting=random.randint(0, 80)
        )

    if settlement.tile.controlled_by.barbaric:
        do_settlement_barbarians(settlement)


def initialize_unit(unit):
    for i in range(unit.generation_size):
        NPC.objects.create(
            name="Soldier {} of {}".format(i, unit),
            male=random.getrandbits(1),
            able=True,
            age_months=20*12,
            origin=unit.location,
            residence=None,
            location=unit.location,
            workplace=None,
            unit=unit,
            trained_soldier=random.getrandbits(4) == 0,
            skill_fighting=random.randint(0, 80)
        )

    unit.generation_size = 0
    unit.save()
