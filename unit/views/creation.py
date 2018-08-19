import math
import random

from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, redirect
from django.views import View

from character.models import CharacterEvent
from unit.models import WorldUnit, unit_cost
from unit.creation import build_population_query_from_request, \
    BadPopulation, sample_candidates, create_unit


class RecruitmentFailure(Exception):
    pass


def get_target_soldier_count(request):
    target_soldier_count = int(request.POST.get('count'))
    if not target_soldier_count > 0:
        raise RecruitmentFailure("Invalid number of soldiers")
    return target_soldier_count


def get_invested_hour_count(request):
    hours_invested = int(request.POST.get('hours_invested'))
    if not hours_invested > 0:
        raise RecruitmentFailure("Invalid hour amount")
    return hours_invested


def get_invested_silver_amount(request):
    silver_invested = int(request.POST.get('silver_invested'))
    if silver_invested < 0:
        raise RecruitmentFailure("Invalid silver amount")
    return silver_invested


def get_unit_type(request):
    unit_type = request.POST.get('unit_type')
    if unit_type not in WorldUnit.get_unit_types(nice=True):
        raise RecruitmentFailure("Invalid unit type")
    return unit_type


def test_if_hero_has_enough_cash_for_soldier_count(hero, target_soldier_count):
    if hero.cash < unit_cost(target_soldier_count):
        raise RecruitmentFailure(
            "You need {} silver coins to recruit a unit of {} soldiers "
            "and you don't have that much.".format(
                target_soldier_count,
                target_soldier_count
            )
        )


def test_if_hero_has_enough_time_remaining(hero, target_soldier_count):
    conscription_time = hero.location.unit_conscription_time(
        target_soldier_count
    )
    if hero.hours_in_turn_left < conscription_time:
        raise RecruitmentFailure(
            "You need {} hours to recruit a unit of {}, but you don't "
            "have that much time left in this turn.".format(
                conscription_time,
                target_soldier_count
            )
        )


def test_if_hero_can_recruit_one_more_unit(hero):
    if hero.worldunit_set.count() + 1 > hero.max_units():
        raise RecruitmentFailure("You can't recruit any more units")


def test_if_hero_can_recruit_soldier_quantity(
        hero, target_soldier_count):
    already_recruited_soldier_count = sum(
        unit.soldier.count()
        for unit in hero.worldunit_set.all()
    )
    if (
            already_recruited_soldier_count + target_soldier_count >
            hero.max_soldiers()
    ):
        raise RecruitmentFailure("You can't recruit that many soldiers")


def test_if_there_are_enough_candidates(candidates, target_soldier_count):
    if candidates.count() < target_soldier_count:
        raise RecruitmentFailure(
            "You are unable to find {} soldiers matching the profile you are "
            "seeking".format(target_soldier_count)
        )


class RecruitmentView(View):
    template_name = 'unit/recruit.html'

    def get(self, request, *args, **kwargs):
        context = {
            'unit_types': WorldUnit.get_unit_types(nice=True)
        }
        return render(request, self.template_name, context)

    @staticmethod
    def fail_post_with_error(request, message):
        messages.error(request, message, extra_tags='danger')
        return redirect('unit:recruit')

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            target_soldier_count = get_target_soldier_count(request)
            unit_type = get_unit_type(request)

            request.hero.can_conscript_unit()
            test_if_hero_has_enough_cash_for_soldier_count(request.hero,
                                                           target_soldier_count)
            test_if_hero_has_enough_time_remaining(
                request.hero, target_soldier_count)
            test_if_hero_can_recruit_one_more_unit(request.hero)
            test_if_hero_can_recruit_soldier_quantity(
                request.hero, target_soldier_count)

            candidates = build_population_query_from_request(
                request, request.hero.location
            )
            test_if_there_are_enough_candidates(
                candidates, target_soldier_count)

            soldiers = sample_candidates(candidates, target_soldier_count)

            unit = create_unit(
                "{}'s unit".format(request.hero),
                request.hero,
                request.hero.location,
                soldiers,
                "conscription",
                unit_type
            )
            unit.mobilize()
            unit.status = WorldUnit.FOLLOWING

            conscription_time_cost = request.hero.location.unit_conscription_time(
                target_soldier_count)
            request.hero.hours_in_turn_left -= conscription_time_cost
            request.hero.cash -= unit.monthly_cost()
            request.hero.save()

            CharacterEvent.objects.create(
                character=request.hero,
                active=False,
                type=CharacterEvent.RECRUIT_UNIT,
                counter=0,
                hour_cost=conscription_time_cost,
                start_turn=request.hero.world.current_turn,
                end_turn=request.hero.world.current_turn,
                settlement=request.hero.location,
                unit=unit
            )

            messages.success(
                request,
                "You conscripted a new unit of {} called {}".format(
                    len(soldiers), unit.name
                ),
                "success"
            )
            return redirect(unit.get_absolute_url())

        except (RecruitmentFailure, BadPopulation) as e:
            return RecruitmentView.fail_post_with_error(request, str(e))


class UnitRaisingView(View):
    template_name = 'unit/raise.html'

    def get(self, request, *args, **kwargs):
        context = {
            'unit_types': WorldUnit.get_unit_types(nice=True),
        }
        return render(request, self.template_name, context)

    @staticmethod
    def fail_post_with_error(request, message):
        messages.error(request, message, extra_tags='danger')
        return redirect('unit:raise')

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            hours_invested = get_invested_hour_count(request)
            silver_invested = get_invested_silver_amount(request)
            unit_type = get_unit_type(request)

            request.hero.can_raise_unit()

            if request.hero.cash < silver_invested:
                raise RecruitmentFailure("You don't have that much silver")
            if request.hero.hours_in_turn_left < hours_invested:
                raise RecruitmentFailure(
                    "You don't have that much hours left this turn")
            test_if_hero_can_recruit_one_more_unit(request.hero)

            amount_candidates_found = math.floor(
                (hours_invested / 100)
                * math.log10(silver_invested + 1)
                * random.random()
            )

            if amount_candidates_found < 1:
                request.hero.hours_in_turn_left -= hours_invested
                request.hero.cash -= silver_invested
                request.hero.save()
                raise RecruitmentFailure(
                    "You did not find any potential comrades. Try again"
                )

            candidates = build_population_query_from_request(
                request, request.hero.location
            )

            soldiers = sample_candidates(candidates, amount_candidates_found)

            test_if_hero_can_recruit_soldier_quantity(
                request.hero, amount_candidates_found)

            unit = create_unit(
                "{}'s unit".format(request.hero),
                request.hero,
                request.hero.location,
                soldiers,
                WorldUnit.RAISED,
                unit_type
            )
            unit.mobilize()
            unit.status = WorldUnit.FOLLOWING

            request.hero.hours_in_turn_left -= hours_invested
            request.hero.cash -= silver_invested
            request.hero.save()

            CharacterEvent.objects.create(
                character=request.hero,
                active=False,
                type=CharacterEvent.RAISE_UNIT,
                counter=0,
                hour_cost=hours_invested,
                start_turn=request.hero.world.current_turn,
                end_turn=request.hero.world.current_turn,
                settlement=request.hero.location,
                unit=unit
            )

            messages.success(
                request,
                "You raised a new unit of {} called {}".format(
                    len(soldiers), unit.name
                ),
                "success"
            )
            return redirect(unit.get_absolute_url())

        except (RecruitmentFailure, BadPopulation) as e:
            return UnitRaisingView.fail_post_with_error(request, str(e))
