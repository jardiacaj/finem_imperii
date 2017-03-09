import json
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models.query_utils import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View

from battle.models import Battle
from decorators import inchar_required
from name_generator.name_generator import NameGenerator
from organization.models import Organization
from world.models import Character, World, Settlement, Tile, WorldUnit
from world.renderer import render_world_for_view
from world.templatetags.extra_filters import nice_hours


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


@inchar_required
def minimap_view(request):
    context = {'world_data': render_world_for_view(request.hero.world)}
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
            'unit_types': WorldUnit.get_unit_types(nice=True)
        }
        return render(request, self.template_name, context)

    @staticmethod
    def fail_post_with_error(request, message):
        messages.add_message(request, messages.ERROR, message, extra_tags='danger')
        return redirect('world:recruit')

    @staticmethod
    def build_population_query(request, prefix):

        candidates = request.hero.location.npc_set.filter(able=True, unit=None)
        if request.POST.get('{}men'.format(prefix)) and request.POST.get('{}women'.format(prefix)):
            pass
        elif request.POST.get('{}men'.format(prefix)) and not request.POST.get('{}women'.format(prefix)):
            candidates = candidates.filter(male=True)
        elif not request.POST.get('{}men'.format(prefix)) and request.POST.get('{}women'.format(prefix)):
            candidates = candidates.filter(male=False)
        elif not request.POST.get('{}men'.format(prefix)) and not request.POST.get('{}women'.format(prefix)):
            raise Exception("You must choose at least one gender.")

        if request.POST.get('{}trained'.format(prefix)) and request.POST.get('{}untrained'.format(prefix)):
            pass
        elif request.POST.get('{}trained'.format(prefix)) and not request.POST.get('{}untrained'.format(prefix)):
            candidates = candidates.filter(trained_soldier=True)
        elif not request.POST.get('{}trained'.format(prefix)) and request.POST.get('{}untrained'.format(prefix)):
            candidates = candidates.filter(trained_soldier=False)
        elif not request.POST.get('{}trained'.format(prefix)) and not request.POST.get('{}untrained'.format(prefix)):
            raise Exception("You must choose at least one training group.")

        skill_queries = []
        if request.POST.get('{}skill_high'.format(prefix)):
            skill_queries.append(Q(skill_fighting__gte=70))
        if request.POST.get('{}skill_medium'.format(prefix)):
            skill_queries.append(Q(skill_fighting__gte=35, skill_fighting__lt=70))
        if request.POST.get('{}skill_low'.format(prefix)):
            skill_queries.append(Q(skill_fighting__lt=35))
        if len(skill_queries) == 0:
            raise Exception("You must choose at least one skill group")

        # See https://stackoverflow.com/questions/852414/how-to-dynamically-compose-an-or-query-filter-in-django
        query = skill_queries.pop()
        for item in skill_queries:
            query |= item
        candidates.filter(query)

        age_queries = []
        if request.POST.get('{}age_old'.format(prefix)):
            age_queries.append(Q(age_months__gte=50*12))
        if request.POST.get('{}age_middle'.format(prefix)):
            age_queries.append(Q(age_months__gte=35*12, age_months__lt=50*12))
        if request.POST.get('{}age_young'.format(prefix)):
            age_queries.append(Q(age_months__gte=18*12, age_months__lt=35*12))
        if request.POST.get('{}age_very_young'.format(prefix)):
            age_queries.append(Q(age_months__gte=12*12, age_months__lt=18*12))
        if len(skill_queries) == 0:
            raise Exception("You must choose at least one age group")

        # See https://stackoverflow.com/questions/852414/how-to-dynamically-compose-an-or-query-filter-in-django
        query = age_queries.pop()
        for item in age_queries:
            query |= item
        candidates.filter(query)

        return candidates

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        recruitment_type = request.POST.get('recruitment_type')
        if recruitment_type in ('conscription', 'professional'):
            if recruitment_type == 'conscription':
                prefix = 'conscript_'
            elif recruitment_type == 'professional':
                prefix = 'professional_'

            # get soldier count
            try:
                target_soldier_count = int(request.POST.get('{}count'.format(prefix)))
                if not target_soldier_count > 0:
                    raise Exception
            except:
                return RecruitmentView.fail_post_with_error(request, "Invalid number of soldiers.")

            # calculate time
            conscription_time = request.hero.location.conscription_time(target_soldier_count)

            if request.hero.hours_in_turn_left < conscription_time:
                return RecruitmentView.fail_post_with_error(
                    request,
                    "You would need {} to do this, but you don't have that much time left in this turn.".format(nice_hours(conscription_time))
                )

            # check unit type
            unit_type = request.POST.get('{}unit_type'.format(prefix))
            if unit_type not in WorldUnit.get_unit_types(nice=True):
                return RecruitmentView.fail_post_with_error(request, "Invalid unit type")

            # check payment
            pay = int(request.POST.get('{}pay'.format(prefix)))
            if pay not in range(1, 7):
                return RecruitmentView.fail_post_with_error(request, "Invalid payment")

            # get candidates
            try:
                candidates = RecruitmentView.build_population_query(request, prefix)
            except Exception as e:
                return RecruitmentView.fail_post_with_error(request, str(e))

            if candidates.count() == 0:
                return RecruitmentView.fail_post_with_error(
                    request,
                    "You seem unable to find anyone in {} matching the profile you want".format(request.hero.location)
                )

            request.hero.hours_in_turn_left -= conscription_time
            request.hero.save()

            unit = WorldUnit.objects.create(
                owner_character=request.hero,
                world=request.hero.world,
                location=request.hero.location,
                name="New unit from {}".format(request.hero.location),
                recruitment_type=recruitment_type,
                type=unit_type,
                status=WorldUnit.NOT_MOBILIZED,
            )

            if target_soldier_count < candidates.count():
                soldiers = random.sample(list(candidates), target_soldier_count)
            else:
                soldiers = list(candidates)

            for soldier in soldiers:
                soldier.unit = unit
                soldier.save()

            messages.success(
                request,
                "You formed a new unit of {} called {}".format(len(soldiers), unit.name),
                "success"
            )
            return redirect('world:recriut')

        else:
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

    def get(self, request, settlement_id=None):
        if settlement_id is not None:
            target_settlement = get_object_or_404(Settlement, id=settlement_id, tile__world_id=request.hero.world_id)

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
        target_settlement = get_object_or_404(
            Settlement,
            id=request.POST.get('target_settlement_id'),
            tile__world_id=request.hero.world_id
        )
        check_result = request.hero.check_travelability(target_settlement)
        if check_result is not None:
            messages.error(request, check_result, extra_tags="danger")
            return redirect('world:travel')

        travel_time = request.hero.travel_time(target_settlement)

        if request.hero.location.tile == target_settlement.tile and travel_time <= request.hero.hours_in_turn_left:
            # travel instantly
            message = request.hero.perform_travel(target_settlement)
            messages.success(request, message, extra_tags="success")
            return redirect('world:travel')
        else:
            messages.success(request, "You you will reach {} when the turn ends.".format(target_settlement), extra_tags="success")
            request.hero.travel_destination = target_settlement
            request.hero.save()
            return redirect('world:travel')


@inchar_required
def travel_view_iframe(request, settlement_id=None):
    if settlement_id is not None:
        target_settlement = get_object_or_404(Settlement, id=settlement_id, tile__world_id=request.hero.world_id)
    else:
        target_settlement = None

    world = request.hero.world
    context = {
        'world': world,
        'regions': render_world_for_view(world),
        'target_settlement': target_settlement,
    }
    return render(request, 'world/travel_map_iframe.html', context)
