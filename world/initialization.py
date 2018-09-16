import random

from django.db import transaction

import world.models.npcs
import world.models.buildings
from context_managers import perf_timer
from finem_imperii.random import WeightedChoice, weighted_choice
from name_generator.name_generator import generate_name
from parallelism import parallel
from world.models.npcs import NPC


class AlreadyInitializedException(Exception):
    pass


def initialize_world(world):
    with perf_timer('Initializing world {} ({})'.format(
            world, world.id)):
        if world.initialized:
            raise AlreadyInitializedException(
                "World {} already initialized!".format(world))

        parallel(initialize_organization, world.organization_set.all()[:])
        parallel(initialize_unit, world.worldunit_set.all()[:])
        parallel(initialize_tile, world.tile_set.all()[:])

        world.initialized = True
        world.save()


def initialize_organization(organization):
    pass


@transaction.atomic
def initialize_tile(tile):
    for settlement in tile.settlement_set.all():
        initialize_settlement(settlement)


def initialize_settlement(settlement):
    with perf_timer('Initializing settlement {} ({}), pop. {}'.format(
            settlement, settlement.id, settlement.population_default)):

        residences = settlement.building_set.filter(
            type=world.models.buildings.Building.RESIDENCE).all()
        fields = settlement.building_set.filter(
            type=world.models.buildings.Building.GRAIN_FIELD).all()
        total_field_workplaces = sum(field.max_workers() for field in fields)
        other_workplaces = settlement.building_set.exclude(
            type__in=(
                world.models.buildings.Building.RESIDENCE,
                world.models.buildings.Building.GRAIN_FIELD
            )
        ).all()
        total_other_workplaces = sum(j.max_workers() for j in other_workplaces)

        settlement.population = settlement.population_default
        settlement.save()

        assigned_workers = 0

        for i in range(settlement.population):
            npc = generate_npc(i, residences, settlement)
            npc.save()

        settlement.building_set.filter(
            type=world.models.buildings.Building.GRAIN_FIELD
        ).update(
            field_production_counter=1500
        )


def generate_npc(i, residences, settlement):
    male = random.getrandbits(1)
    name = generate_name(male)
    over_sixty = (random.getrandbits(4) == 0)
    if over_sixty:
        age_months = random.randint(60 * 12, 90 * 12)
        able = random.getrandbits(1)
    else:
        age_months = random.randint(0, 60 * 12)
        able = (random.getrandbits(7) != 0)
    residence_choices = [
        WeightedChoice(value=residence, weight=residence.quantity)
        for residence in residences
    ]
    npc = NPC.objects.create(
        name=name,
        male=male,
        able=able,
        age_months=age_months,
        residence=weighted_choice(residence_choices),
        origin=settlement,
        location=settlement,
        workplace=None,
        unit=None,
        trained_soldier=(random.getrandbits(
            4) == 0) if age_months >= world.models.npcs.NPC.VERY_YOUNG_AGE_LIMIT else False,
        skill_fighting=random.randint(0, 80)
    )
    return npc


@transaction.atomic
def initialize_unit(unit):
    with perf_timer('Initializing unit {} ({})'.format(
            unit, unit.id)):
        for i in range(unit.generation_size):
            world.models.npcs.NPC.objects.create(
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
