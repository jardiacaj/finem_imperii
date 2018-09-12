import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View

from account.user_functions import can_create_character
from character.models import Character
from messaging import shortcuts
from name_generator.name_generator import get_names, get_surnames
from organization.models.organization import Organization
from world.models.geography import World, Settlement
from world.models.items import InventoryItem


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
            'Welcome, {}'.format(character),
            {
                'state': state,
                'character': character
            }
        )

        if not state.barbaric:
            message = shortcuts.create_message(
                'messaging/messages/new_character.html',
                world,
                "New member",
                {
                    'character': character,
                    'organization': state
                },
                link=character.get_absolute_url()
            )
            shortcuts.add_organization_recipient(message, state)

        state.character_members.add(character)

        return redirect(character.activation_url)