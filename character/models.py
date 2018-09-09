import math

from django.contrib.auth.models import User
from django.db import models, transaction

from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

import organization.models.capability
import organization.models.organization
from mixins import AdminURLMixin
from world.models import items, geography
import unit.models
from battle.models import BattleCharacter
from messaging import shortcuts
from messaging.models import CharacterMessage


class CharacterEvent(models.Model):
    class Meta:
        ordering = ['create_timestamp']

    RECRUIT_UNIT = 'recruit_unit'
    TRAVEL = 'travel'
    PAUSE = 'pause'
    UNPAUSE = 'unpause'
    RAISE_UNIT = 'raise_unit'
    BUREAUCRATIC_WORK = 'bureaucratic_work'
    ARREST_WARRANT = 'arrest_warrant'

    TYPE_CHOICES = (
        (RECRUIT_UNIT, RECRUIT_UNIT),
        (TRAVEL, TRAVEL),
        (PAUSE, PAUSE),
        (UNPAUSE, UNPAUSE),
        (RAISE_UNIT, RAISE_UNIT),
        (BUREAUCRATIC_WORK, BUREAUCRATIC_WORK),
        (ARREST_WARRANT, ARREST_WARRANT),
    )

    character = models.ForeignKey('Character', models.CASCADE)
    create_timestamp = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES,
                            db_index=True)
    counter = models.IntegerField(blank=True, null=True,
                                  help_text='Counter for general use')
    hour_cost = models.IntegerField(blank=True, null=True, default=None)
    start_turn = models.IntegerField()
    end_turn = models.IntegerField(blank=True, null=True)
    unit = models.ForeignKey('unit.WorldUnit', models.SET_NULL, blank=True,
                             null=True)
    settlement = models.ForeignKey('world.Settlement', models.SET_NULL,
                                   blank=True, null=True)
    organization = models.ForeignKey('organization.Organization',
                                     models.SET_NULL,
                                     blank=True, null=True)

    actions = {
        TRAVEL: {
            'url': '/character/travel',
            'condition': lambda character: character.can_travel(),
            'common': True,
            'nice_name': 'Travel',
            'html': 'Traveled to {event.settlement}'
        },
        PAUSE: {
            'url': '/character/pause',
            'condition': lambda character: character.can_pause(),
            'common': False,
            'nice_name': 'Pause',
            'html': 'Character paused'
        },
        UNPAUSE: {
            'url': '/character/unpause',
            'condition': lambda character: character.can_unpause(),
            'common': False,
            'nice_name': 'Unpause',
            'html': 'Character unpaused'
        },
        RECRUIT_UNIT: {
            'url': '/unit/recruit',
            'condition': lambda
                character: character.can_conscript_unit(),
            'common': True,
            'nice_name': 'Recruit',
            'html': 'Recruited unit {event.unit}'
        },
        RAISE_UNIT: {
            'url': '/unit/raise',
            'condition': lambda
                character: character.can_raise_unit(),
            'common': True,
            'nice_name': 'Raise unit',
            'html': 'Raised unit {event.unit}'
        },
        BUREAUCRATIC_WORK: {
            'url': '/character/bureaucratic_work',
            'condition': lambda
                character: character.can_do_bureaucratic_work(),
            'common': True,
            'nice_name': 'Bureaucratic work',
            'html': 'Public order work in {event.settlement}'
        },
    }

    def get_html(self):
        return CharacterEvent.actions[self.type].get('html').format(
            event=self
        )


class Character(models.Model, AdminURLMixin):
    COMMANDER = 'commander'
    TRADER = 'trader'
    BUREAUCRAT = 'bureaucrat'
    PROFILE_CHOICES = (
        (COMMANDER, COMMANDER),
        (TRADER, TRADER),
        (BUREAUCRAT, BUREAUCRAT),
    )

    name = models.CharField(max_length=100)
    world = models.ForeignKey('world.World', models.PROTECT)
    location = models.ForeignKey('world.Settlement', models.PROTECT)
    oath_sworn_to = models.ForeignKey(
        'organization.Organization',
        null=True, blank=True,
        on_delete=models.DO_NOTHING
    )
    owner_user = models.ForeignKey(User, models.CASCADE)
    cash = models.IntegerField(default=0)
    hours_in_turn_left = models.IntegerField(default=15 * 24)
    travel_destination = models.ForeignKey(
        'world.Settlement',
        null=True, blank=True, related_name='travellers_heading',
        on_delete=models.SET_NULL
    )
    profile = models.CharField(max_length=20, choices=PROFILE_CHOICES)
    last_activation_time = models.DateTimeField(default=timezone.now)
    paused = models.BooleanField(default=False)

    @property
    def activation_url(self):
        return reverse('character:activate', kwargs={'char_id': self.id})

    def inactivity_time(self):
        return timezone.now() - self.last_activation_time

    def hours_since_last_activation(self):
        return self.inactivity_time().total_seconds() / 60 / 60

    def maybe_pause_for_inactivity(self):
        if not self.can_pause():
            return

        if self.hours_since_last_activation() > \
                self.inactivity_hours_allowed():
            self.pause()

    def inactivity_hours_allowed(self):
        time_since_user_registered = (
                timezone.now() - self.owner_user.date_joined)
        hours_since_user_registered = (
                time_since_user_registered.total_seconds() / 60 / 60)
        return 24 * 2 if hours_since_user_registered < 24 * 5 else 24 * 6

    def hours_until_autopause(self):
        inactivity_hours_allowed = self.inactivity_hours_allowed()
        hours_since_last_activation = self.hours_since_last_activation()
        return max(
            inactivity_hours_allowed - hours_since_last_activation,
            0
        )

    @transaction.atomic()
    def pause(self):
        self.oath_sworn_to = self.get_violence_monopoly()
        self.save()

        for unit in self.worldunit_set.all():
            unit.disband()

        while self.organization_set.exclude(
                id=self.world.get_barbaric_state().id
        ).exists():
            organization = self.organization_set.exclude(
                id=self.world.get_barbaric_state().id)[0]
            organization.remove_member(self)

            message = shortcuts.create_message(
                'messaging/messages/character_paused.html',
                self.world,
                'pause',
                {'character': self},
                link=self.get_absolute_url()
            )
            shortcuts.add_organization_recipient(
                message,
                organization,
                add_lead_organizations=True
            )

            self.refresh_from_db()

        self.last_activation_time = timezone.now()
        self.paused = True
        self.save()

        CharacterEvent.objects.create(
            character=self,
            active=False,
            type=CharacterEvent.PAUSE,
            counter=0,
            hour_cost=None,
            start_turn=self.world.current_turn,
            end_turn=self.world.current_turn
        )

    def can_pause(self):
        return not self.paused

    def can_unpause(self):
        return self.paused and self.hours_since_last_activation() > 24 * 5

    def unpause(self):
        self.paused = False
        self.oath_sworn_to.character_members.add(self)
        self.world.get_barbaric_state().character_members.remove(self)
        self.save()

        CharacterEvent.objects.create(
            character=self,
            active=False,
            type=CharacterEvent.UNPAUSE,
            counter=0,
            hour_cost=None,
            start_turn=self.world.current_turn,
            end_turn=self.world.current_turn
        )

        message = shortcuts.create_message(
            'messaging/messages/character_unpaused.html',
            self.world,
            'pause',
            {'character': self},
            link=self.get_absolute_url()
        )
        shortcuts.add_organization_recipient(
            message,
            self.get_violence_monopoly(),
            add_lead_organizations=True
        )

    def get_battle_participating_in(self):
        try:
            return BattleCharacter.objects.get(
                character=self,
                battle_organization__side__battle__current=True
            ).battle_organization.side.battle
        except BattleCharacter.DoesNotExist:
            return None

    def travel_time(self, target_settlement):
        distance = self.location.distance_to(target_settlement)
        if (
                self.location.tile.type == geography.Tile.MOUNTAIN
                or target_settlement.tile.type == geography.Tile.MOUNTAIN
        ):
            distance *= 2
        if self.location.tile.get_current_battles().exists():
            distance *= 2
        days = distance / 100 * 2
        return math.ceil(days * 24)

    def can_travel(self):
        if self.get_battle_participating_in() is not None:
            return False
        return True

    def check_travelability(self, target_settlement):
        if not self.can_travel():
            return "You can't currently travel " \
                   "(are you taking part in battle?)"
        if target_settlement == self.location:
            return "You can't travel to {} as you are already there.".format(
                target_settlement
            )
        if target_settlement.tile.distance_to(self.location.tile) > 1.5:
            return "You can only travel to contiguous regions."
        if (
                self.travel_destination is not None
                and self.travel_destination != target_settlement
        ):
            return "You cant travel to {} because you are already travelling" \
                   " to {}.".format(
                target_settlement,
                self.travel_destination
            )
        return None

    @transaction.atomic
    def perform_travel(self, destination):
        for travelling_unit in self.worldunit_set.filter(
                status=unit.models.WorldUnit.FOLLOWING,
                location=self.location
        ):
            travelling_unit.location = destination
            travelling_unit.save()

        travel_time = self.travel_time(destination)
        self.location = destination
        self.hours_in_turn_left -= travel_time
        self.save()

        CharacterEvent.objects.create(
            character=self,
            active=False,
            type=CharacterEvent.TRAVEL,
            counter=0,
            hour_cost=travel_time,
            start_turn=self.world.current_turn,
            end_turn=self.world.current_turn,
            settlement=destination
        )

        return travel_time, destination

    @transaction.atomic
    def add_notification(self, template, category, template_context=None):
        if template_context is None:
            template_context = {}
        message = shortcuts.create_message(
            template=template,
            world=self.world,
            category=category,
            template_context=template_context
        )
        shortcuts.add_character_recipient(message, self)

    def get_violence_monopoly(self):
        try:
            return self.organization_set.get(violence_monopoly=True)
        except organization.models.organization.Organization.DoesNotExist:
            return None

    def unread_messages(self):
        return CharacterMessage.objects.filter(
            messagerecipient__character=self, messagerecipient__read=False
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('character:character', kwargs={'character_id': self.id})

    def get_html_name(self):
        result = self.name
        for membership in self.organization_set.all():
            result += membership.get_bootstrap_icon()
        return result

    def get_html_link(self):
        return format_html(
            '<a href="{url}">{name}</a>',
            url=mark_safe(self.get_absolute_url()),
            name=mark_safe(self.get_html_name())
        )

    @staticmethod
    def total_carrying_capacity():
        return 100

    def remaining_carrying_capacity(self):
        return self.total_carrying_capacity() - self.carrying_weight()

    def carrying_items(self):
        return items.InventoryItem.objects.filter(
            owner_character=self,
            location=None
        )

    def carrying_weight(self):
        weight = 0
        for item in self.carrying_items():
            weight += item.quantity * item.get_weight()
        return weight

    def can_take_grain_from_public_granary(self):
        return self.can_use_capability_in_current_location(
            organization.models.capability.Capability.TAKE_GRAIN
        )

    def can_conscript_unit(self):
        return (
                self.can_use_capability_in_current_location(
                    organization.models.capability.Capability.CONSCRIPT
                )
                and
                self.get_battle_participating_in() is None
        )

    def max_amount_of_conscripted_soldiers(self):
        return math.floor(min(
            self.cash,
            (self.hours_in_turn_left - self.location.base_unit_conscription_cost()) * 5
        ))

    def can_use_capability_in_current_location(self, capability_type):
        local_violence_monopoly = \
            self.location.tile.controlled_by.get_violence_monopoly()

        organizations_local_vm = local_violence_monopoly. \
            organizations_character_can_apply_capabilities_to_this_with(
            self, capability_type)
        organizations_controlled_by = self.location.tile.controlled_by \
            .organizations_character_can_apply_capabilities_to_this_with(
            self, capability_type)
        return (
                organizations_local_vm
                or
                organizations_controlled_by
        )

    def takeable_grain_from_public_granary(self):
        if not self.can_take_grain_from_public_granary():
            return 0

        return min(
            self.remaining_carrying_capacity(),
            self.hours_in_turn_left * self.inventory_bushels_per_hour(),

            self.location.get_default_granary().
            get_public_bushels_object().quantity
        )

    def inventory_bushels_per_hour(self):
        if self.profile == Character.TRADER:
            return 4
        return 2

    def inventory_object(self, type):
        try:
            return items.InventoryItem.objects.get(
                type=type,
                owner_character=self,
                location=None
            )
        except items.InventoryItem.DoesNotExist:
            return None

    def carrying_quantity(self, type):
        inventory_object = self.inventory_object(type)
        if inventory_object is None:
            return 0
        else:
            return inventory_object.quantity

    def add_to_inventory(self, type, quantity):
        inventory_object = self.inventory_object(type)
        if inventory_object is None:
            items.InventoryItem.objects.create(
                type=type,
                owner_character=self,
                quantity=quantity
            )
        else:
            inventory_object.quantity += quantity
            inventory_object.save()

    def max_units(self):
        if self.profile == Character.COMMANDER:
            return 10
        return 3

    def max_soldiers(self):
        if self.profile == Character.COMMANDER:
            return 5000
        return 500

    def can_do_bureaucratic_work(self):
        return (
                self.profile == self.BUREAUCRAT and
                self.get_battle_participating_in() is None
        )

    def can_raise_unit(self):
        return True

    def possible_common_actions(self):
        return ((name, descriptor) for (name, descriptor) in
                CharacterEvent.actions.items() if
                descriptor.get('common') and
                descriptor.get('condition')(self))

    def possible_actions(self):
        return ((name, descriptor) for (name, descriptor) in
                CharacterEvent.actions.items() if
                descriptor.get('condition')(self))
