from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, redirect
from django.views import View

from unit.models import WorldUnit, unit_cost
from unit.recruitment import build_population_query_from_request, \
    BadPopulation, sample_candidates, recruit_unit


class RecruitmentFailure(Exception):
    pass


def test_if_hero_can_conscript(hero):
    if not hero.has_conscripting_capability_in_current_location():
        raise RecruitmentFailure("You can't conscript units here")


def get_soldier_count(request):
    target_soldier_count = int(request.POST.get('count'))
    if not target_soldier_count > 0:
        raise RecruitmentFailure("Invalid number of soldiers")
    return target_soldier_count


def get_unit_type(request):
    unit_type = request.POST.get('unit_type')
    if unit_type not in WorldUnit.get_unit_types(nice=True):
        raise RecruitmentFailure("Invalid unit type")
    return unit_type


def test_if_hero_has_enough_cash(hero, target_soldier_count):
    if hero.cash < unit_cost(target_soldier_count):
        raise RecruitmentFailure(
            "You need {} silver coins to recruit a unit of {} soldiers "
            "and you don't have that much.".format(
                target_soldier_count,
                target_soldier_count
            )
        )


def test_if_hero_has_enough_time_remaining(hero, target_soldier_count):
    conscription_time = hero.location.conscription_time(
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
            'unit_types': WorldUnit.get_unit_types(nice=True),
            'can_recruit': request.hero.has_conscripting_capability_in_current_location()
        }
        return render(request, self.template_name, context)

    @staticmethod
    def fail_post_with_error(request, message):
        messages.error(request, message, extra_tags='danger')
        return redirect('unit:recruit')

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            target_soldier_count = get_soldier_count(request)
            unit_type = get_unit_type(request)

            test_if_hero_can_conscript(request.hero)
            test_if_hero_has_enough_cash(request.hero, target_soldier_count)
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

            unit = recruit_unit(
                "{}'s unit".format(request.hero),
                request.hero,
                request.hero.location,
                soldiers,
                "conscription",
                unit_type
            )
            unit.mobilize()
            unit.status = WorldUnit.FOLLOWING

            request.hero.hours_in_turn_left -= request.hero.location.\
                conscription_time(target_soldier_count)
            request.hero.cash -= unit.monthly_cost()
            request.hero.save()

            messages.success(
                request,
                "You formed a new unit of {} called {}".format(
                    len(soldiers), unit.name
                ),
                "success"
            )
            return redirect(unit.get_absolute_url())

        except (RecruitmentFailure, BadPopulation) as e:
            return RecruitmentView.fail_post_with_error(request, str(e))
