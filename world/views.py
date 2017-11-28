import random

import math
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http.response import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic.base import View

from account.user_functions import can_create_character
from battle.models import Order, Battle
from decorators import inchar_required
from messaging import shortcuts
from messaging.models import MessageRelationship
from name_generator.name_generator import get_names, get_surnames
from organization.models import Organization, Capability
from world.models import Character, World, Settlement, WorldUnit, \
    WorldUnitStatusChangeException, Tile, TileEvent, InventoryItem, unit_cost
from world.recruitment import build_population_query_from_request, \
    BadPopulation, sample_candidates, recruit_unit
from world.renderer import render_world_for_view
from world.templatetags.extra_filters import nice_hours
from world.turn import field_output_months


@inchar_required
def world_view(request, world_id):
    world = get_object_or_404(World, id=world_id)
    context = {
        'world': world,
        'battles': Battle.objects.filter(
            tile__world=world,
            current=True
        )
    }
    return render(request, 'world/view_world.html', context)


@inchar_required
def world_view_iframe(request, world_id):
    world = get_object_or_404(World, id=world_id)
    context = {
        'world': world,
        'regions': render_world_for_view(world)
    }
    return render(request, 'world/view_world_iframe.html', context)


@inchar_required
def tile_view(request, tile_id):
    tile = get_object_or_404(Tile, id=tile_id, world=request.hero.world)
    context = {
        'tile': tile,
        'harvest': (tile.world.current_turn % 12) in field_output_months,
        'characters': Character.objects.filter(location__tile=tile, paused=False),
        'units': WorldUnit.objects.filter(location__tile=tile),
        'conquests': TileEvent.objects.filter(
            tile=tile, type=TileEvent.CONQUEST, end_turn__isnull=True)
    }
    return render(request, 'world/view_tile.html', context)


@inchar_required
def tile_view_iframe(request, tile_id):
    tile = get_object_or_404(Tile, id=tile_id, world=request.hero.world)
    context = {
        'tile': tile,
        'regions': render_world_for_view(tile.world)
    }
    return render(request, 'world/view_tile_iframe.html', context)


@inchar_required
def minimap_view(request):
    context = {'world_data': render_world_for_view(request.hero.world)}
    return render(request, 'world/minimap_iframe.html', context)


@login_required
def create_character(request):
    if not can_create_character(request.user):
        raise Http404()

    context = {
        'worlds': World.objects.all()
    }
    return render(
        request, 'world/create_character_step1.html', context=context)


class CharacterCreationView(View):
    template_name = 'world/create_character.html'

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
        return redirect('world:create_character', world_id=world_id)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if not can_create_character(request.user):
            raise Http404()

        try:
            world_id = kwargs['world_id']
            world = World.objects.get(id=world_id)
        except World.DoesNotExist:
            messages.add_message(request, request.ERROR, "Invalid World")
            return redirect('world:create_character')

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


class RecruitmentView(View):
    template_name = 'world/recruit.html'

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
        return redirect('world:recruit')

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
                    "You need {} to recruit a unit of {}, but you don't have "
                    "that much time left in this turn.".format(
                        nice_hours(conscription_time),
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


@login_required
def activate_character(request, char_id):
    character = get_object_or_404(
        Character, pk=char_id, owner_user=request.user)
    request.session['character_id'] = character.id
    character.last_activation_time = timezone.now()
    character.save()
    return redirect('world:character_home')


@login_required
@require_POST
def pause_character(request):
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
def unpause_character(request):
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
    return render(request, 'world/character_home.html', context=context)


class TravelView(View):
    template_name = 'world/travel.html'

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
                return redirect('world:travel')

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
            return redirect('world:travel')

        target_settlement = get_object_or_404(
            Settlement,
            id=settlement_id,
            tile__world_id=request.hero.world_id
        )
        check_result = request.hero.check_travelability(target_settlement)
        if check_result is not None:
            messages.error(request, check_result, extra_tags="danger")
            return redirect('world:travel')

        travel_time = request.hero.travel_time(target_settlement)

        if request.hero.location.tile == target_settlement.tile and \
                        travel_time <= request.hero.hours_in_turn_left:
            # travel instantly
            message = request.hero.perform_travel(target_settlement)
            messages.success(request, message, extra_tags="success")
            return redirect('world:travel')
        else:
            messages.success(
                request,
                "You you will reach {} when the turn ends.".format(
                    target_settlement),
                extra_tags="success"
            )
            request.hero.travel_destination = target_settlement
            request.hero.save()
            return redirect('world:travel')


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
    return render(request, 'world/travel_map_iframe.html', context)


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
    return render(request, 'world/view_unit.html', context)


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
    return redirect(reverse('world:character_home'))


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
    return redirect(reverse('world:character_home'))


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
    return render(request, 'world/view_character.html', context=context)


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
    return render(request, 'world/view_character_iframe.html', context)


class InventoryView(View):
    template_name = 'world/view_inventory.html'

    def get(self, request):

        context = {
            'can_take_grain': request.hero.
                can_take_grain_from_public_granary(),
            'carrying_grain': request.hero.carrying_quantity(
                InventoryItem.GRAIN
            ),
            'takeable_grain': request.hero.takeable_grain_from_public_granary()
        }
        return render(request, 'world/view_inventory.html', context=context)

    @staticmethod
    def fail_post_with_error(request, message):
        messages.add_message(
            request, messages.ERROR, message, extra_tags='danger'
        )
        return redirect('world:inventory')

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
        return redirect('world:inventory')


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
        return redirect('world:inventory')

    if transfer_cash_amount > request.hero.cash:
        messages.error(
            request,
            "You have not enough cash.",
            "danger"
        )
        return redirect('world:inventory')

    if transfer_cash_amount < 1:
        messages.error(
            request,
            "That is not a valid cash amount.",
            "danger"
        )
        return redirect('world:inventory')

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

    return redirect('world:inventory')
