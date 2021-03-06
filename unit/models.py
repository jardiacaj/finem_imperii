from django.db import models

from django.db.models import Avg, F, Sum
from django.db.transaction import atomic
from django.urls import reverse
from django.utils.html import format_html

import character.models
from battle.models import BattleUnit
from mixins import AdminURLMixin


class WorldUnitStatusChangeException(Exception):
    pass


class WorldUnit(models.Model, AdminURLMixin):
    CONSCRIPTED = 'conscripted'
    PROFESSIONAL = 'professional'
    MERCENARY = 'mercenary'
    RAISED = 'raised'
    RECRUITMENT_CHOICES = (
        (CONSCRIPTED, CONSCRIPTED),
        (PROFESSIONAL, PROFESSIONAL),
        (MERCENARY, MERCENARY),
        (RAISED, RAISED),
    )

    LIGHT_INFANTRY = 'light infantry soldiers'
    PIKEMEN = 'pikemen'
    ARCHERS = 'archers'
    CAVALRY = 'cavalry'
    CATAPULT = 'catapult'
    SIEGE_TOWER = 'siege tower'
    RAM = 'ram'
    TYPE_CHOICES = (
        (LIGHT_INFANTRY, LIGHT_INFANTRY),
        (PIKEMEN, PIKEMEN),
        (ARCHERS, ARCHERS),
        (CAVALRY, CAVALRY),
        (CATAPULT, CATAPULT),
        (SIEGE_TOWER, SIEGE_TOWER),
        (RAM, RAM),
    )

    NOT_MOBILIZED = 'not mobilized'
    TRAINING = 'training'
    STANDING = 'standing'
    FOLLOWING = 'following'
    CUSTOMER_SEARCH = 'customer search'
    REGROUPING = 'regrouping'
    STATUS_CHOICES = (
        (NOT_MOBILIZED, NOT_MOBILIZED),
        (TRAINING, TRAINING),
        (STANDING, STANDING),
        (FOLLOWING, FOLLOWING),
        (CUSTOMER_SEARCH, CUSTOMER_SEARCH),
    )

    LINE_CHOICES = (
        (0, "advanced line"),
        (1, "front line"),
        (2, "middle line"),
        (3, "rear line"),
        (4, "rearguard"),
    )

    SIDE_CHOICES = (
        (-5, "flanking far left"),
        (-4, "flanking left"),
        (-3, "cover left flank"),
        (-2, "left side"),
        (-1, "left-center"),
        (0, "center"),
        (1, "right-center"),
        (2, "right side"),
        (3, "cover right flank"),
        (4, "flanking right"),
        (5, "flanking far right"),
    )

    owner_character = models.ForeignKey(
        'character.Character',
        models.SET_NULL,
        blank=True, null=True)
    world = models.ForeignKey('world.World', models.SET_NULL, blank=True,
                              null=True)
    location = models.ForeignKey('world.Settlement', models.SET_NULL,
                                 blank=True, null=True)
    name = models.CharField(max_length=100)
    recruitment_type = models.CharField(
        max_length=30, choices=RECRUITMENT_CHOICES
    )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    mobilization_status_since = models.IntegerField()
    current_status_since = models.IntegerField()
    battle_line = models.IntegerField(choices=LINE_CHOICES, default=3)
    battle_side_pos = models.IntegerField(choices=SIDE_CHOICES, default=0)
    generation_size = models.IntegerField(
        default=0, help_text="Only used in tests that need generated units"
    )
    default_battle_orders = models.ForeignKey('battle.Order', models.PROTECT)
    auto_pay = models.BooleanField(default=False,
                                   help_text="Unit is paid automatically from character cash each turn.")

    @staticmethod
    def get_unit_types(nice=False):
        return (unit_type[1 if nice else 0]
                for unit_type in WorldUnit.TYPE_CHOICES)

    @staticmethod
    def get_unit_states(nice=False):
        return (state[1 if nice else 0] for state in WorldUnit.STATUS_CHOICES)

    def is_ranged(self):
        return self.type in (self.ARCHERS, self.CATAPULT)

    def starting_ammo(self):
        if self.type == self.ARCHERS:
            return 24
        return 0

    def shot_range(self):
        if self.type == self.ARCHERS:
            return 5
        return 0

    def get_owners_debt(self):
        return self.soldier.aggregate(Sum('unit_debt'))['unit_debt__sum']

    def monthly_cost(self):
        return self.soldier.count()

    def __str__(self):
        return self.name

    def get_short_html_descriptor(self):
        return format_html(
            '{} <span class="unit-icon-{}" aria-hidden="true"></span>',
            self.soldier.count(),
            self.type
        )

    def get_long_html_descriptor(self):
        return format_html(
            '{} <span class="unit-icon-{}" aria-hidden="true"></span> {}',
            self.soldier.count(),
            self.type,
            self.name
        )

    def get_html_link(self):
        return format_html('{descriptor} <a href="{url}">{name}</a>',
                           descriptor=self.get_short_html_descriptor(),
                           url=self.get_absolute_url(),
                           name=self.name
                           )

    def get_absolute_url(self):
        return reverse('unit:unit', kwargs={'unit_id': self.id})

    def average_fighting_skill(self):
        return round(
            self.soldier.all().aggregate(
                Avg('skill_fighting')
            )['skill_fighting__avg']
        )

    def change_status(self, new_status):
        if (
                self.owner_character.profile != character.models.Character.COMMANDER and
                self.owner_character.location != self.location
        ):
            raise WorldUnitStatusChangeException(
                "You can't change the unit's status while being "
                "in a different location (only commanders can "
                "do that)."
            )
        if new_status not in WorldUnit.get_unit_states():
            raise WorldUnitStatusChangeException(
                "Invalid unit status {}".format(new_status)
            )
        if self.status == WorldUnit.CUSTOMER_SEARCH:
            raise WorldUnitStatusChangeException(
                "Mercenaries can't change_status()"
            )
        if new_status == WorldUnit.CUSTOMER_SEARCH:
            raise WorldUnitStatusChangeException(
                "Can't switch to searching customer status"
            )
        if self.get_current_battle() is not None:
            raise WorldUnitStatusChangeException(
                "Can't change status while in battle"
            )
        if self.status == new_status:
            raise WorldUnitStatusChangeException(
                "The unit is already {}".format(self.get_status_display())
            )
        if (new_status == WorldUnit.FOLLOWING
                and self.owner_character.location != self.location):
            raise WorldUnitStatusChangeException(
                "A unit can only follow you if you are in the same location."
            )
        if new_status == WorldUnit.NOT_MOBILIZED:
            if self.mobilization_status_since == self.world.current_turn:
                raise WorldUnitStatusChangeException(
                    "Cannot demobilize {} the same turn it has been"
                    " mobilized".format(self)
                )
            self.demobilize()
        if (new_status != WorldUnit.NOT_MOBILIZED
                and self.status == WorldUnit.NOT_MOBILIZED):
            if self.mobilization_status_since == self.world.current_turn:
                raise WorldUnitStatusChangeException(
                    "Cannot mobilize {} the same turn it has been"
                    " demobilized".format(self)
                )
            self.mobilize()
        self.status = new_status
        self.save()

    @atomic
    def mobilize(self):
        self.mobilization_status_since = self.world.current_turn
        self.save()
        self.soldier.update(
            residence=None,
            location=None,
            workplace=None
        )

    @atomic
    def demobilize(self):
        self.mobilization_status_since = self.world.current_turn
        self.status = WorldUnit.NOT_MOBILIZED
        self.soldier.update(
            location=F('origin'),
        )
        self.save()

    def get_fighting_soldiers(self):
        return self.soldier.filter(able=True)

    def get_current_battle(self):
        try:
            in_battle = BattleUnit.objects.get(
                world_unit=self,
                battle_side__battle__current=True,
                in_battle=True
            )
            return in_battle.battle_side.battle
        except BattleUnit.DoesNotExist:
            pass

    def get_violence_monopoly(self):
        if self.owner_character:
            return self.owner_character.get_violence_monopoly()
        else:
            return self.world.get_barbaric_state()

    def disband(self):
        self.demobilize()
        self.soldier.update(unit=None)
        self.owner_character = None
        self.location = None
        self.world = None
        self.save()

    @atomic
    def pay_debt(self, payer):
        payer.cash -= self.get_owners_debt()
        payer.save()
        self.soldier.update(unit_debt=0)
        self.save()
