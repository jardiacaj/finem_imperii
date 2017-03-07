import json
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View

from battle.models import Battle
from decorators import inchar_required
from name_generator.name_generator import NameGenerator
from organization.models import Organization
from world.models import Character, World, Settlement, Tile, WorldUnit
from world.renderer import render_world_for_view


def world_view(request, world_id):
    world = get_object_or_404(World, id=world_id)
    context = {
        'world': world,
    }
    return render(request, 'world/view_world.html', context)


def world_view_iframe(request, world_id):
    world = get_object_or_404(World, id=world_id)
    context = {
        'world': world,
        'regions': render_world_for_view(world)
    }
    return render(request, 'world/view_world_iframe.html', context)


def minimap_view(request, world_id, tile_id=None, settlement_id=None):
    world = get_object_or_404(World, id=world_id)
    tile = None if tile_id is None else get_object_or_404(Tile, id=tile_id)
    settlement = None if settlement_id is None else get_object_or_404(Settlement, id=settlement_id)
    context = {
        'world': world,
        'focused_tile': tile,
        'focused_settlement': settlement,
        'regions': render_world_for_view(world)
    }
    return render(request, 'world/minimap_iframe.html', context)


@login_required
def create_character(request):
    context = {
        'worlds': World.objects.all()
    }
    return render(request, 'world/create_character_step1.html', context=context)


class CharacterCreationView(View):
    template_name = 'world/create_character.html'

    def get(self, request, *args, **kwargs):
        name_generator = NameGenerator()
        return render(request, self.template_name, {
            'world': get_object_or_404(World, id=kwargs['world_id']),
            'names': name_generator.get_names(limit=100),
            'surnames': name_generator.get_surnames(limit=100),
        })

    @staticmethod
    def fail_post_with_error(request, world_id, message):
        messages.add_message(request, messages.ERROR, message, extra_tags='danger')
        return redirect('world:create_character', world_id=world_id)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            world_id = kwargs['world_id']
            world = World.objects.get(id=world_id)
        except World.DoesNotExist:
            messages.add_message(request, request.ERROR, "Invalid World")
            return redirect('world:create_character')

        try:
            state_id = request.POST.get('state_id')
            state = None if state_id == '0' else Organization.objects.get(id=state_id)
        except Organization.DoesNotExist:
            return self.fail_post_with_error(request, world_id, "Select a valid state")

        name = request.POST.get('name')
        surname = request.POST.get('surname')

        name_generator = NameGenerator()
        if name not in name_generator.get_names() or surname not in name_generator.get_surnames():
            return self.fail_post_with_error(request, world_id, "Select a valid name/surname")

        character = Character.objects.create(
            name=name + ' ' + surname,
            world=world,
            location=random.choice(
                Settlement.objects.filter(tile__controlled_by=state) if state is not None else Settlement.objects.filter(tile__world=world)
            ),
            oath_sworn_to=None if state is None else state if state.leader is None else state.leader,
            owner_user=request.user,
            cash=0
        )

        if state:
            state.members.add(character)

        return redirect(character.activation_url)


class RecruitmentView(View):
    template_name = 'world/recruit.html'

    def get(self, request, *args, **kwargs):
        context = {
            'unit_types': (unit_type[1] for unit_type in WorldUnit.TYPE_CHOICES)
        }
        return render(request, self.template_name, context)

    @staticmethod
    def fail_post_with_error(request, message):
        messages.add_message(request, messages.ERROR, message, extra_tags='danger')
        return redirect('world:recruit')

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        pass


@login_required
def activate_character(request, char_id):
    character = get_object_or_404(Character, pk=char_id, owner_user=request.user)
    request.session['character_id'] = character.id
    return redirect('world:character_home')


@inchar_required
def character_home(request):
    return render(request, 'world/character_home.html')


@inchar_required
def setup_battle(request, rival_char_id=None):
    if rival_char_id is None:
        rivals = Character.objects.exclude(pk=request.hero.pk)
        return render(request, 'world/setup_battle.html', context={'rivals': rivals})
    else:
        if rival_char_id == request.hero.id:
            messages.error(request, "Cannot battle yourself!", extra_tags="danger")
            return setup_battle(request)
        rival = get_object_or_404(Character, id=rival_char_id)
        battle = Battle()
        battle.save()
        battle.start_battle(request.hero, rival)

        return redirect(reverse('battle:setup', kwargs={'battle_id': battle.id}))


class TravelView(View):
    template_name = 'world/travel.html'

    @staticmethod
    def check(request, target_settlement):
        if target_settlement == request.hero.location:
            messages.error(
                request,
                "You can't travel to {} as you are already there.".format(target_settlement),
                extra_tags="danger"
            )
            return redirect('world:travel')
        if target_settlement.tile.distance_to(request.hero.location.tile) > 1.5:
            messages.error(
                request,
                "You can only travel to contiguous regions.".format(target_settlement),
                extra_tags="danger"
            )
            return redirect('world:travel')

    def get(self, request, settlement_id=None):
        if settlement_id is not None:
            target_settlement = get_object_or_404(Settlement, id=settlement_id, tile__world_id=request.hero.world_id)

            check_result = self.check(request, target_settlement)
            if check_result is not None:
                return check_result

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
        target_settlement = get_object_or_404(
            Settlement,
            id=request.POST.get('target_settlement_id'),
            tile__world_id=request.hero.world_id
        )
        check_result = self.check(request, target_settlement)
        if check_result is not None:
            return check_result
        travel_time = request.hero.travel_time(target_settlement)

        if request.hero.location.tile == target_settlement.tile and travel_time <= request.hero.hours_in_turn_left:
            # travel instantly
            request.hero.location = target_settlement
            request.hero.hours_in_turn_left -= travel_time
            request.hero.save()
            messages.success(request, "You are now in {}".format(target_settlement), extra_tags="success")
            return redirect('world:travel')
        else:
            pass


@inchar_required
def travel_view_iframe(request, settlement_id=None):
    world = request.hero.world
    context = {
        'world': world,
        'regions': render_world_for_view(world),
        'focused_tile': request.hero.location.tile,
        'focused_settlement': request.hero.location,
    }
    return render(request, 'world/travel_map_iframe.html', context)
