import logging
import random

from django.db import transaction

from name_generator.name_generator import NameGenerator
from organization.models import Organization
from world.models import Building, NPC


class AlreadyInitializedException(Exception):
    pass


class WorldInitializer:
    def __init__(self, world):
        self.world = world
        self.name_generator = NameGenerator()

    @transaction.atomic
    def initialize(self):
        logging.info("Initializing world {}".format(self.world))
        if self.world.initialized:
            raise AlreadyInitializedException("World {} already initialized!".format(self.world))
        for organization in self.world.organization_set.all():
            self.initialize_organization(organization)
        for tile in self.world.tile_set.all():
            self.initialize_tile(tile)
        self.world.initialized = True
        self.world.save()

    def initialize_organization(self, organization):
        if organization.position_type == Organization.ELECTED and not organization.character_members.exists():
            organization.next_election = self.world.current_turn + 3

    def initialize_tile(self, tile):
        logging.info("Initializing tile {}".format(tile))
        for settlement in tile.settlement_set.all():
            self.initialize_settlement(settlement)

    def initialize_settlement(self, settlement):
        logging.info("Initializing settlement {}".format(settlement))
        residences = settlement.building_set.filter(type=Building.RESIDENCE).all()
        fields = settlement.building_set.filter(type=Building.GRAIN_FIELD).all()
        total_field_workplaces = sum(field.max_employment() for field in fields)
        other_workplaces = settlement.building_set.exclude(type__in=(Building.RESIDENCE, Building.GRAIN_FIELD)).all()
        total_other_workplaces = sum(j.max_employment() for j in other_workplaces)

        assigned_workers = 0

        for i in range(settlement.population):
            male = random.getrandbits(1)
            name = self.name_generator.generate_name(male)

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
                        cumulative += field.max_employment()
                        if pos < cumulative:
                            break
                    workplace = field
                else:
                    pos = random.randint(0, total_other_workplaces)
                    cumulative = 0
                    for other_workplace in other_workplaces:
                        cumulative += other_workplace.max_employment()
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
