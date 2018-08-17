import random

from django.db import models

import world.models.buildings
import world.models.geography
from battle.models import BattleSoldierInTurn


class NPCManager(models.Manager):
    def gender_distribution(self):
        return {
            'female': self.get_queryset().filter(male=False).count(),
            'male': self.get_queryset().filter(male=True).count()
        }

    def skill_distribution(self):
        return {
            'high skill': self.get_queryset().filter(
                skill_fighting__gte=NPC.TOP_SKILL_LIMIT
            ).count(),
            'medium skill': self.get_queryset().filter(
                skill_fighting__gte=NPC.MEDIUM_SKILL_LIMIT,
                skill_fighting__lt=NPC.TOP_SKILL_LIMIT
            ).count(),
            'low skill': self.get_queryset().filter(
                skill_fighting__lt=NPC.MEDIUM_SKILL_LIMIT
            ).count(),
        }

    def age_distribution(self):
        return {
            'too young': self.get_queryset().filter(
                age_months__lt=NPC.VERY_YOUNG_AGE_LIMIT
            ).count(),
            'very young': self.get_queryset().filter(
                age_months__gte=NPC.VERY_YOUNG_AGE_LIMIT,
                age_months__lt=NPC.YOUNG_AGE_LIMIT
            ).count(),
            'young': self.get_queryset().filter(
                age_months__gte=NPC.YOUNG_AGE_LIMIT,
                age_months__lt=NPC.MIDDLE_AGE_LIMIT
            ).count(),
            'middle age': self.get_queryset().filter(
                age_months__gte=NPC.MIDDLE_AGE_LIMIT,
                age_months__lt=NPC.OLD_AGE_LIMIT
            ).count(),
            'old': self.get_queryset().filter(
                age_months__gte=NPC.OLD_AGE_LIMIT
            ).count(),
        }

    def professionality_distribution(self):
        return {
            'professional':
                self.get_queryset().filter(trained_soldier=True).count(),
            'non-professional':
                self.get_queryset().filter(trained_soldier=False).count()
        }

    def origin_distribution(self):
        result = {}
        for npc in self.get_queryset().all():
            result[npc.origin.name] = result.get(npc.origin.name, 0) + 1
        return result


class NPC(models.Model):
    class Meta:
        base_manager_name = 'stats_manager'
        index_together = (
            ('residence', 'hunger')
        )

    stats_manager = NPCManager()
    objects = models.Manager()

    TOP_SKILL_LIMIT = 70
    MEDIUM_SKILL_LIMIT = 35

    OLD_AGE_LIMIT = 50 * 12
    MIDDLE_AGE_LIMIT = 35 * 12
    YOUNG_AGE_LIMIT = 18 * 12
    VERY_YOUNG_AGE_LIMIT = 12 * 12

    name = models.CharField(max_length=100)
    male = models.BooleanField()
    able = models.BooleanField()
    age_months = models.IntegerField()
    origin = models.ForeignKey('world.Settlement', models.PROTECT,
                               related_name='offspring')
    residence = models.ForeignKey(
        'world.Building', models.SET_NULL, null=True, blank=True,
        related_name='resident'
    )
    location = models.ForeignKey('world.Settlement', models.PROTECT,
                                 null=True, blank=True)
    workplace = models.ForeignKey(
        'world.Building', models.SET_NULL, null=True, blank=True,
        related_name='worker'
    )
    unit = models.ForeignKey(
        'unit.WorldUnit', models.SET_NULL, null=True, blank=True,
        related_name='soldier'
    )
    trained_soldier = models.BooleanField(default=None)
    skill_fighting = models.IntegerField()
    wound_status = models.SmallIntegerField(
        choices=BattleSoldierInTurn.WOUND_STATUS_CHOICES,
        default=BattleSoldierInTurn.UNINJURED
    )
    hunger = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    def take_hit(self):
        if self.wound_status == BattleSoldierInTurn.DEAD:
            return
        self.wound_status += 1
        self.save()
        if self.wound_status == BattleSoldierInTurn.DEAD:
            self.die()
        self.ability_roll()

    def ability_roll(self):
        if self.wound_status == BattleSoldierInTurn.MEDIUM_WOUND:
            if random.getrandbits(3) == 0:
                self.able = False
                self.save()
        if self.wound_status == BattleSoldierInTurn.HEAVY_WOUND:
            if random.getrandbits(1) == 0:
                self.able = False
                self.save()

    def die(self):
        unit = self.unit
        self.location = None
        self.residence = None
        self.unit = None
        self.able = False
        self.save()

        if unit and unit.soldier.count() == 0:
            unit.disband()

    def get_health_icon(self):
        return "●◕◑◔☠"[self.wound_status]

    def get_age(self):
        return int(self.age_months / 12)

    def get_skill_display(self):
        return "high" if self.skill_fighting > NPC.TOP_SKILL_LIMIT else \
            "medium" if self.skill_fighting > NPC.MEDIUM_SKILL_LIMIT else \
                "low"

    def get_hunger_display(self):
        return "satiated" if self.hunger <= 0 else \
            "hungry" if self.hunger == 1 else \
                "very hungry" if self.hunger in (2, 3) else \
                    "starving"
