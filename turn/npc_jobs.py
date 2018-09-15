import random

from django.db import transaction

from context_managers import perf_timer
from finem_imperii.random import WeightedChoice, weighted_choice
from parallelism import parallel
from world.models.buildings import Building
from world.models.geography import World, Settlement
from world.models.npcs import NPC


def worldwide_npc_job_updates(world: World):
    parallel(
        settlement_job_updates,
        Settlement.objects.filter(tile__world=world)[:]
    )


@transaction.atomic
def settlement_job_updates(settlement: Settlement):
    with perf_timer("NPC Job updates {}".format(settlement)):
        settlement.get_residents().filter(able=False).update(workplace=None)
        npcs_looking_for_a_job = settlement.get_residents().filter(
            workplace=None,
            age_months__gt=NPC.VERY_YOUNG_AGE_LIMIT
        )
        fields = list(settlement.building_set.filter(
            type=Building.GRAIN_FIELD,
            owner=None
        ))
        field_choices = [
            WeightedChoice(value=field, weight=field.quantity)
            for field in fields
        ]

        for jobseeker in npcs_looking_for_a_job:
            jobseeker.workplace = weighted_choice(field_choices)
            jobseeker.save()

        guild_workers = settlement.get_residents().filter(
            workplace__type=Building.GUILD
        )
        field_workers = settlement.get_residents().filter(
            workplace__type=Building.GRAIN_FIELD
        )

        if not settlement.tile.controlled_by.get_violence_monopoly().barbaric:
            if settlement.guilds_setting == Settlement.GUILDS_PROHIBIT:
                for guild_worker in guild_workers:
                    guild_worker.workplace = weighted_choice(field_choices)
                    guild_worker.save()
            elif settlement.guilds_setting == Settlement.GUILDS_RESTRICT:
                num_guild_workers_to_remove = max(
                    10,
                    int(guild_workers.count() * 0.03)
                )
                if num_guild_workers_to_remove > guild_workers.count():
                    num_guild_workers_to_remove = guild_workers.count()
                guild_workers_list = list(guild_workers)
                for guild_worker in random.sample(
                        guild_workers_list,
                        num_guild_workers_to_remove
                ):
                    guild_worker.workplace = weighted_choice(field_choices)
                    guild_worker.save()
            elif settlement.guilds_setting == Settlement.GUILDS_KEEP:
                pass
            elif settlement.guilds_setting == Settlement.GUILDS_PROMOTE:
                num_guild_workers_to_add = max(
                    10,
                    int(guild_workers.count() * 0.03)
                )
                if num_guild_workers_to_add > field_workers.count():
                    num_guild_workers_to_add = field_workers.count()
                field_workers_list = list(field_workers)
                for field_worker in random.sample(
                        field_workers_list,
                        num_guild_workers_to_add
                ):
                    field_worker.workplace = settlement.building_set.get(
                        type=Building.GUILD
                    )
                    field_worker.save()
