from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from decorators import inchar_required
from world.models.geography import Settlement
from world.renderer import render_world_for_view


class TravelView(View):
    template_name = 'character/travel.html'

    def get(self, request, settlement_id=None):
        context = {
            'hide_sidebar': True,
            'target_settlement': None
        }

        if settlement_id is not None:
            target_settlement = get_object_or_404(
                Settlement,
                id=settlement_id,
                tile__world_id=request.hero.world_id
            )

            check_result = request.hero.check_travelability(target_settlement)
            if check_result is not None:
                messages.error(request, check_result, extra_tags="danger")
                return redirect('character:travel')

            travel_time = request.hero.travel_time(target_settlement)

            context['target_settlement'] = target_settlement
            context['travel_time'] = travel_time

        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        settlement_id = int(request.POST.get('target_settlement_id'))

        if settlement_id == 0 and request.hero.travel_destination:
            messages.success(request, "OK.", extra_tags="success")
            request.hero.travel_destination = None
            request.hero.save()
            return redirect('character:travel')

        target_settlement = get_object_or_404(
            Settlement,
            id=settlement_id,
            tile__world_id=request.hero.world_id
        )
        check_result = request.hero.check_travelability(target_settlement)
        if check_result is not None:
            messages.error(request, check_result, extra_tags="danger")
            return redirect('character:travel')

        travel_time = request.hero.travel_time(target_settlement)

        if request.hero.location.tile == target_settlement.tile and \
                        travel_time <= request.hero.hours_in_turn_left:
            # travel instantly
            request.hero.perform_travel(target_settlement)
            message = "After travelling for {} hours you reached {}.".format(
                travel_time,
                target_settlement
            )
            messages.success(request, message, extra_tags="success")
            return redirect('character:travel')
        else:
            messages.success(
                request,
                "You you will reach {} when the turn ends.".format(
                    target_settlement),
                extra_tags="success"
            )
            request.hero.travel_destination = target_settlement
            request.hero.save()
            return redirect('character:travel')


@inchar_required
def travel_view_iframe(request, settlement_id=None):
    if settlement_id is not None:
        target_settlement = get_object_or_404(
            Settlement,
            id=settlement_id,
            tile__world_id=request.hero.world_id
        )
    else:
        target_settlement = None

    world = request.hero.world
    context = {
        'world': world,
        'world_data': render_world_for_view(world),
        'target_settlement': target_settlement,
    }
    return render(request, 'character/travel_map_iframe.html', context)