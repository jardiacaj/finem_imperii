import random
from enum import Enum

from django.db.models.query_utils import Q

import world.models.npcs
from battle.models import Order
from unit.models import WorldUnit


class Gender(Enum):
    FEMALE, MALE = range(2)


class Training(Enum):
    TRAINED, UNTRAINED = range(2)


class Skill(Enum):
    HIGH, MEDIUM, LOW = range(3)


class Age(Enum):
    VERY_YOUNG, YOUNG, MIDDLE, OLD = range(4)


flag_types = {
    'gender': Gender,
    'training': Training,
    'skill': Skill,
    'age': Age
}

flag_queries = {
    Gender.FEMALE: Q(male=False),
    Gender.MALE: Q(male=True),
    Training.TRAINED: Q(trained_soldier=True),
    Training.UNTRAINED: Q(trained_soldier=False),
    Skill.HIGH: Q(skill_fighting__gte=world.models.npcs.NPC.TOP_SKILL_LIMIT),
    Skill.MEDIUM: Q(
        skill_fighting__gte=world.models.npcs.NPC.MEDIUM_SKILL_LIMIT,
        skill_fighting__lt=world.models.npcs.NPC.TOP_SKILL_LIMIT),
    Skill.LOW: Q(skill_fighting__lt=world.models.npcs.NPC.MEDIUM_SKILL_LIMIT),
    Age.VERY_YOUNG: Q(
        age_months__gte=world.models.npcs.NPC.VERY_YOUNG_AGE_LIMIT,
        age_months__lt=world.models.npcs.NPC.YOUNG_AGE_LIMIT),
    Age.YOUNG: Q(
        age_months__gte=world.models.npcs.NPC.YOUNG_AGE_LIMIT,
        age_months__lt=world.models.npcs.NPC.MIDDLE_AGE_LIMIT),
    Age.MIDDLE: Q(
        age_months__gte=world.models.npcs.NPC.MIDDLE_AGE_LIMIT,
        age_months__lt=world.models.npcs.NPC.OLD_AGE_LIMIT),
    Age.OLD: Q(age_months__gte=world.models.npcs.NPC.OLD_AGE_LIMIT)
}

request_fields = {
    Gender.FEMALE: 'women',
    Gender.MALE: 'men',
    Training.TRAINED: 'trained',
    Training.UNTRAINED: 'untrained',
    Skill.HIGH: 'skill_high',
    Skill.MEDIUM: 'skill_medium',
    Skill.LOW: 'skill_low',
    Age.VERY_YOUNG: 'age_very_young',
    Age.YOUNG: 'age_young',
    Age.MIDDLE: 'age_middle',
    Age.OLD: 'age_old',
}


class BadPopulation(Exception):
    pass


def build_population_query_from_request(request, location):
    args = {}
    for arg_name, arg_type in flag_types.items():
        arg = []
        for arg_element in arg_type:
            request_field = request_fields[arg_element]
            if request.POST.get(request_field) is not None:
                arg.append(arg_element)
        args[arg_name] = arg
    return build_population_query(location, **args)


def all_recruitable_soldiers_in_settlement(location):
    return location.npc_set.filter(able=True, unit=None)


def build_population_query(location, **kwargs):
    candidates = all_recruitable_soldiers_in_settlement(location)

    for arg_name, arg_values in kwargs.items():
        qs = []
        for arg_element in arg_values:
            qs.append(flag_queries[arg_element])

        if len(qs) == 0:
            raise BadPopulation('No {} selected'.format(arg_name))

        query = qs.pop()
        for item in qs:
            query |= item
        candidates = candidates.filter(query)
    return candidates


def sample_candidates(candidates, target_soldier_count):
    if target_soldier_count < candidates.count():
        return random.sample(list(candidates), target_soldier_count)
    else:
        return list(candidates)


def create_unit(name, owner, location, soldiers, recruitment_type, unit_type):
    orders = Order.objects.create(what=Order.STAND)

    unit = WorldUnit.objects.create(
        owner_character=owner,
        world=location.tile.world,
        origin=location,
        location=location,
        name=name,
        recruitment_type=recruitment_type,
        type=unit_type,
        status=WorldUnit.STANDING,
        mobilization_status_since=location.tile.world.current_turn - 1,
        current_status_since=location.tile.world.current_turn - 1,
        default_battle_orders=orders
    )

    for soldier in soldiers:
        soldier.unit = unit
        soldier.save()

    return unit
