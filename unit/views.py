from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from django.views import View
from django.views.decorators.http import require_POST

from battle.models import Order
from decorators import inchar_required

from unit.models import WorldUnit, unit_cost, WorldUnitStatusChangeException
from unit.recruitment import build_population_query_from_request, \
    BadPopulation, sample_candidates, recruit_unit
from world.models import TileEvent


class RecruitmentView(View):
    template_name = 'unit/recruit.html'

    def get(self, request, *args, **kwargs):
        context = {
            'unit_types': WorldUnit.get_unit_types(nice=True),
            'can_recruit': request.hero.can_conscript()
        }
        return render(request, self.template_name, context)

    @staticmethod
    def fail_post_with_error(request, message):
        messages.add_message(
            request, messages.ERROR, message, extra_tags='danger'
        )
        return redirect('unit:recruit')

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        recruitment_type = request.POST.get('recruitment_type')
        if recruitment_type in ('conscription', 'professional'):
            if recruitment_type == 'conscription':
                prefix = 'conscript_'
            elif recruitment_type == 'professional':
                prefix = 'professional_'
            else:
                raise Http404()

            if not request.hero.can_conscript():
                return RecruitmentView.fail_post_with_error(
                    request,
                    "You can't conscript units here."
                )

            # get soldier count
            target_soldier_count = \
                int(request.POST.get('{}count'.format(prefix)))
            if not target_soldier_count > 0:
                return RecruitmentView.fail_post_with_error(
                    request, "Invalid number of soldiers."
                )

            # check cash
            if request.hero.cash < unit_cost(target_soldier_count):
                return RecruitmentView.fail_post_with_error(
                    request,
                    "You need {} silver coins to recruit a unit of {} "
                    "and you don't have that much.".format(
                        target_soldier_count,
                        target_soldier_count
                    )
                )

            # calculate time
            conscription_time = request.hero.location.conscription_time(
                target_soldier_count
            )

            if request.hero.hours_in_turn_left < conscription_time:
                return RecruitmentView.fail_post_with_error(
                    request,
                    "You need {} hours to recruit a unit of {}, but you don't "
                    "have that much time left in this turn.".format(
                        conscription_time,
                        target_soldier_count
                    )
                )

            # check unit type
            unit_type = request.POST.get('{}unit_type'.format(prefix))
            if unit_type not in WorldUnit.get_unit_types(nice=True):
                return RecruitmentView.fail_post_with_error(
                    request, "Invalid unit type."
                )

            # check payment
            """
            pay = int(request.POST.get('{}pay'.format(prefix)))
            if pay not in range(1, 7):
                return RecruitmentView.fail_post_with_error(
                    request, "Invalid payment."
                )

            if (
                    request.hero.worldunit_set.count() + 1 >
                    request.hero.max_units()
            ):
                return RecruitmentView.fail_post_with_error(
                    request, "You can't recruit any more units."
                )
            """

            already_recruited_soldier_count = sum(
                unit.soldier.count()
                for unit in request.hero.worldunit_set.all()
            )
            if (
                    already_recruited_soldier_count + target_soldier_count >
                    request.hero.max_soldiers()
            ):
                return RecruitmentView.fail_post_with_error(
                    request, "You can't recruit that many soldiers."
                )


            # get candidates

            try:
                candidates = build_population_query_from_request(
                    request, prefix, request.hero.location
                )
            except BadPopulation as e:
                return RecruitmentView.fail_post_with_error(request, e)

            if candidates.count() == 0:
                return RecruitmentView.fail_post_with_error(
                    request,
                    "You seem unable to find anyone in {} matching the profile"
                    " you want".format(request.hero.location)
                )

            soldiers = sample_candidates(candidates, target_soldier_count)

            unit = recruit_unit(
                "{}'s new unit".format(request.hero),
                request.hero,
                request.hero.location,
                soldiers,
                recruitment_type,
                unit_type
            )
            unit.mobilize()

            request.hero.hours_in_turn_left -= conscription_time
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

        else:
            pass


@inchar_required
@require_POST
def unit_battle_orders(request, unit_id):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        owner_character=request.hero
    )
    battle_orders = request.POST['battle_orders']
    if battle_orders not in [order[0] for order in Order.WHAT_CHOICES]:
        raise Http404("Invalid orders")
    unit.default_battle_orders = Order.objects.create(what=battle_orders)
    unit.save()
    return redirect(request.META.get('HTTP_REFERER', unit.get_absolute_url()))


@inchar_required
@require_POST
def unit_status_change(request, unit_id, new_status):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        owner_character=request.hero
    )
    try:
        unit.change_status(new_status)
    except WorldUnitStatusChangeException as e:
        messages.error(request, str(e), "danger")
    return redirect(request.META.get('HTTP_REFERER', unit.get_absolute_url()))


@inchar_required
@require_POST
def unit_conquest_action(request, unit_id):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        owner_character=request.hero
    )
    tile_event = get_object_or_404(
        TileEvent,
        end_turn__isnull=True,
        type=TileEvent.CONQUEST,
        tile=unit.location.tile,
        organization_id=request.POST.get('conqueror_id')
    )
    hours = int(request.POST.get('hours'))
    if unit.status == WorldUnit.NOT_MOBILIZED:
        messages.error(request, "Unit not movilized")
    elif unit.location != request.hero.location:
        messages.error(request, "You must be in the same region to do this.")
    elif not 0 < hours <= request.hero.hours_in_turn_left:
        messages.error(request, "Invalid number of hours")
    elif request.POST.get('action') == "support":
        tile_event.counter += unit.get_fighting_soldiers().count() * hours // (15*24)
        request.hero.hours_in_turn_left -= hours
        request.hero.save()
        tile_event.save()
    elif request.POST.get('action') == "counter":
        tile_event.counter -= unit.get_fighting_soldiers().count() * hours // (15*24)
        request.hero.hours_in_turn_left -= hours
        request.hero.save()
        tile_event.save()
    else:
        messages.error(request, "Invalid action")

    return redirect(request.META.get('HTTP_REFERER', unit.get_absolute_url()))


@inchar_required
def unit_disband(request, unit_id):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        owner_character=request.hero
    )
    unit.disband()
    messages.success(request, 'Your unit has been disbanded.', 'success')
    return redirect(reverse('character:character_home'))


@inchar_required
def unit_view(request, unit_id):
    unit = get_object_or_404(WorldUnit, id=unit_id)
    context = {
        'unit': unit,
        'origins': unit.soldier.origin_distribution(),
        'conquests': TileEvent.objects.filter(
            tile=unit.location.tile,
            type=TileEvent.CONQUEST,
            end_turn__isnull=True
        )
    }
    return render(request, 'unit/view_unit.html', context)


@inchar_required
def unit_rename(request, unit_id):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        owner_character=request.hero
    )
    if request.POST.get('name'):
        unit.name = request.POST.get('name')
        unit.save()
    return redirect(request.META.get('HTTP_REFERER', unit.get_absolute_url()))


@inchar_required
@require_POST
def unit_battle_settings(request, unit_id):
    unit = get_object_or_404(
        WorldUnit,
        id=unit_id,
        owner_character=request.hero
    )
    battle_line = int(request.POST['battle_line'])
    battle_side_pos = int(request.POST['battle_side_pos'])
    if not 0 <= battle_line < 5 or not -5 <= battle_side_pos <= 5:
        raise Http404("Invalid settings")
    unit.battle_side_pos = battle_side_pos
    unit.battle_line = battle_line
    unit.save()
    return redirect(request.META.get('HTTP_REFERER', unit.get_absolute_url()))