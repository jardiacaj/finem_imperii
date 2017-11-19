import math
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST

from account.user_functions import can_create_character
from character.models import Character
from decorators import inchar_required
from messaging import shortcuts
from messaging.models import MessageRelationship
from name_generator.name_generator import get_names, get_surnames
from organization.models import Organization
from world.models import World, Settlement, InventoryItem
from world.renderer import render_world_for_view


@login_required
def create(request):
    if not can_create_character(request.user):
        raise Http404()

    context = {
        'worlds': World.objects.all()
    }
    return render(
        request, 'character/create_step1.html', context=context)


class CharacterCreationView(View):
    template_name = 'character/create_step2.html'

    def get(self, request, *args, **kwargs):
        if not can_create_character(request.user):
            raise Http404()

        return render(request, self.template_name, {
            'world': get_object_or_404(World, id=kwargs['world_id']),
            'names': get_names(limit=100),
            'surnames': get_surnames(limit=100),
        })

    @staticmethod
    def fail_post_with_error(request, world_id, message):
        messages.add_message(
            request, messages.ERROR, message, extra_tags='danger')
        return redirect('character:create', world_id=world_id)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if not can_create_character(request.user):
            raise Http404()

        try:
            world_id = kwargs['world_id']
            world = World.objects.get(id=world_id)
        except World.DoesNotExist:
            messages.add_message(request, request.ERROR, "Invalid World")
            return redirect('character:create')

        try:
            state_id = request.POST.get('state_id')
            state = Organization.objects.get(id=state_id)
        except Organization.DoesNotExist:
            return self.fail_post_with_error(
                request, world_id, "Select a valid Realm"
            )

        name = request.POST.get('name')
        surname = request.POST.get('surname')

        if name not in get_names() or surname not in get_surnames():
            return self.fail_post_with_error(
                request, world_id, "Select a valid name/surname"
            )

        profile = request.POST.get('profile')
        if profile not in (choice[0] for choice in Character.PROFILE_CHOICES):
            return self.fail_post_with_error(
                request, world_id, "Select a valid profile"
            )

        character = Character.objects.create(
            name=name + ' ' + surname,
            world=world,
            location=random.choice(
                Settlement.objects.filter(
                    tile__in=state.get_all_controlled_tiles()
                )
            ),
            oath_sworn_to=state if state.leader is None else state.leader,
            owner_user=request.user,
            cash=100,
            profile=profile
        )

        if character.profile == Character.TRADER:
            InventoryItem.objects.create(
                type=InventoryItem.CART,
                quantity=5,
                owner_character=character,
            )

        character.add_notification(
            'messaging/messages/welcome.html',
            'welcome',
            {
                'state': state,
                'character': character
            }
        )

        if not state.barbaric:
            message = shortcuts.create_message(
                'messaging/messages/new_character.html',
                world,
                "newcomer",
                {
                    'character': character,
                    'organization': state
                },
                link=character.get_absolute_url()
            )
            shortcuts.add_organization_recipient(message, state)

        state.character_members.add(character)

        return redirect(character.activation_url)


@login_required
def activate(request, char_id):
    character = get_object_or_404(
        Character, pk=char_id, owner_user=request.user)
    request.session['character_id'] = character.id
    character.last_activation_time = timezone.now()
    character.save()
    return redirect('character:character_home')


@login_required
@require_POST
def pause(request):
    character = get_object_or_404(
        Character,
        pk=request.POST.get('character_id'),
        owner_user=request.user
    )
    if character.can_pause():
        character.pause()
        messages.success(
            request,
            "{} has been paused.".format(character),
            "success"
        )
    else:
        messages.error(
            request,
            "{} can't be paused.".format(character),
            "danger"
        )
    return redirect('account:home')


@login_required
@require_POST
def unpause(request):
    character = get_object_or_404(
        Character,
        pk=request.POST.get('character_id'),
        owner_user=request.user
    )
    if character.can_unpause():
        character.unpause()
        messages.success(
            request,
            "{} has been unpaused.".format(character),
            "success"
        )
    else:
        messages.error(
            request,
            "{} can't be unpaused.".format(character),
            "danger"
        )
    return redirect('account:home')


@inchar_required
def character_home(request):
    context = {
        'recipient_list': request.hero.messagerecipient_set.filter(read=False)
    }
    return render(request, 'character/character_home.html', context=context)


class TravelView(View):
    template_name = 'character/travel.html'

    def get(self, request, settlement_id=None):
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
            context = {
                'target_settlement': target_settlement,
                'travel_time': travel_time
            }
        else:
            context = {'target_settlement': None}

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
        'regions': render_world_for_view(world),
        'target_settlement': target_settlement,
    }
    return render(request, 'character/travel_map_iframe.html', context)


@inchar_required
@require_POST
def public_order(request):
    if not request.hero.can_work_public_order():
        raise Http404("Can't do that")

    hours = int(request.POST.get('hours'))

    if hours < 1 or hours > request.hero.hours_in_turn_left:
        messages.error(request, 'You can\'t work that many ours.', 'danger')

    po_improvement = math.floor(
        hours / request.hero.location.population * 500
    )
    new_po = min(request.hero.location.public_order + po_improvement, 1000)

    message = 'You worked {} hours, improving the public order in ' \
              '{} from {}% to {}%' \
              ''.format(
                    hours,
                    request.hero.location,
                    request.hero.location.public_order / 10,
                    new_po / 10
              )

    request.hero.location.public_order = new_po
    request.hero.location.save()
    request.hero.hours_in_turn_left -= hours
    request.hero.save()

    messages.success(request, message, 'success')
    return redirect(reverse('character:character_home'))


@inchar_required
def character_view(request, character_id):
    character = get_object_or_404(
        Character,
        id=character_id,
        world=request.hero.world
    )
    favourite = MessageRelationship.objects.filter(
        from_character=request.hero,
        to_character=character
    ).exists()
    context = {
        'character': character,
        'favourite': favourite
    }
    return render(request, 'character/view_character.html', context=context)


@inchar_required
def character_view_iframe(request, character_id):
    character = get_object_or_404(
        Character,
        id=character_id,
        world=request.hero.world
    )
    context = {
        'character': character,
        'regions': render_world_for_view(character.world),
    }
    return render(request,
                  'character/view_character_iframe.html', context)


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