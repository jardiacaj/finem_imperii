import math

from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.decorators.http import require_POST

from character.models import Character
from decorators import inchar_required
from messaging import shortcuts
from world.models.items import InventoryItem


class InventoryView(View):
    template_name = 'character/view_inventory.html'

    def get(self, request):

        context = {
            'can_take_grain': request.hero.
                can_take_grain_from_public_granary(),
            'carrying_grain': request.hero.carrying_quantity(
                InventoryItem.GRAIN
            ),
            'takeable_grain': request.hero.takeable_grain_from_public_granary()
        }
        return render(request, 'character/view_inventory.html', context=context)

    @staticmethod
    def fail_post_with_error(request, message):
        messages.add_message(
            request, messages.ERROR, message, extra_tags='danger'
        )
        return redirect('character:inventory')

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        bushels_to_transfer = int(request.POST.get('bushels'))
        hours_needed = math.ceil(
            bushels_to_transfer / request.hero.inventory_bushels_per_hour()
        )
        if request.hero.hours_in_turn_left < hours_needed:
            return self.fail_post_with_error(
                request, "You don't have enough time left this turn.")
        if bushels_to_transfer < 1:
            raise Http404()
        if action == 'load':
            if bushels_to_transfer > request.hero.takeable_grain_from_public_granary():
                return self.fail_post_with_error(
                    request, "You can't take that many bushels")
            granary_bushels = request.hero.location.get_default_granary().\
                get_public_bushels_object()
            granary_bushels.quantity -= bushels_to_transfer
            granary_bushels.save()
            request.hero.add_to_inventory(
                InventoryItem.GRAIN, bushels_to_transfer
            )
        elif action == 'unload':
            if bushels_to_transfer > request.hero.carrying_quantity(
                InventoryItem.GRAIN
            ):
                return self.fail_post_with_error(
                    request, "You don't have that many bushels")
            hero_inv_obj = request.hero.inventory_object(InventoryItem.GRAIN)
            hero_inv_obj.quantity -= bushels_to_transfer
            if hero_inv_obj.quantity == 0:
                hero_inv_obj.delete()
            else:
                hero_inv_obj.save()
            granary_bushels = request.hero.location.get_default_granary(). \
                get_public_bushels_object()
            granary_bushels.quantity += bushels_to_transfer
            granary_bushels.save()
        else:
            raise Http404()
        request.hero.hours_in_turn_left -= hours_needed
        request.hero.save()
        return redirect('character:inventory')


@inchar_required
@require_POST
def transfer_cash(request):
    transfer_cash_amount = int(request.POST.get('transfer_cash_amount'))

    to_character = get_object_or_404(
        Character,
        pk=request.POST.get('to_character_id')
    )

    if request.hero.location != to_character.location:
        messages.error(
            request,
            "You need to be in the same location to transfer money.",
            "danger"
        )
        return redirect('character:inventory')

    if transfer_cash_amount > request.hero.cash:
        messages.error(
            request,
            "You have not enough cash.",
            "danger"
        )
        return redirect('character:inventory')

    if transfer_cash_amount < 1:
        messages.error(
            request,
            "That is not a valid cash amount.",
            "danger"
        )
        return redirect('character:inventory')

    request.hero.cash = request.hero.cash - transfer_cash_amount
    to_character.cash = to_character.cash + transfer_cash_amount

    request.hero.save()
    to_character.save()

    messages.success(
        request,
        "The transaction was successful.",
        "success"
    )

    message = shortcuts.create_message(
        'messaging/messages/cash_received.html',
        request.hero.world,
        "cash transfer",
        {
            'sender': request.hero,
            'amount': transfer_cash_amount
        }
    )
    shortcuts.add_character_recipient(message, to_character)

    return redirect('character:inventory')