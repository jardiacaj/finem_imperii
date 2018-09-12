from context_managers import perf_timer
from turn.barbarians import worldwide_barbarian_generation
from turn.battle import worldwide_trigger_battles, worldwide_battle_joins, \
    worldwide_battle_starts, worldwide_battle_turns
from turn.building_production import worldwide_building_production
from turn.character import worldwide_pause_characters, \
    worldwide_character_travels, \
    worldwide_restore_character_hours
from turn.conquest import worldwide_conquests
from turn.demography import worldwide_food_consumption, \
    worldwide_population_changes
from turn.elections import worldwide_elections
from turn.npc_jobs import worldwide_npc_job_updates
from turn.public_order import worldwide_public_order
from turn.taxes import worldwide_taxes
from turn.unit import worldwide_unit_maintenance


def pass_turn(world):
    with perf_timer('Turn in {} ({})'.format(
            world, world.id)):

        with perf_timer('Block world'):
            world.blocked_for_turn = True
            world.save()

        # with perf_timer('Delete dead realms'):
        #    worldwide_delete_dead_realms(world)
        with perf_timer('Pause characters'):
            worldwide_pause_characters(world)
        with perf_timer('Travels'):
            worldwide_character_travels(world)
        with perf_timer('Restore character hours'):
            worldwide_restore_character_hours(world)
        with perf_timer('Unit maintenance'):
            worldwide_unit_maintenance(world)
        with perf_timer('Battle starts'):
            worldwide_battle_starts(world)
        with perf_timer('Battle joins'):
            worldwide_battle_joins(world)
        with perf_timer('Battle turns'):
            worldwide_battle_turns(world)
        with perf_timer('Battle triggers'):
            worldwide_trigger_battles(world)
        with perf_timer('Elections'):
            worldwide_elections(world)
        with perf_timer('Conquests'):
            worldwide_conquests(world)
        with perf_timer('Barbarian generation'):
            worldwide_barbarian_generation(world)
        # with perf_timer('NPC resicence assignment'):
        #     worldwide_npc_residence_assignment()
        with perf_timer('NPC job updates'):
            worldwide_npc_job_updates(world)
        with perf_timer('Building production'):
            worldwide_building_production(world)
        # with perf_timer('Trade'):
        #     worldiwde_trade()
        with perf_timer('Food consumption'):
            worldwide_food_consumption(world)
        with perf_timer('Population changes'):
            worldwide_population_changes(world)
        # with perf_timer('Food spoilage'):
        #     worldwide_food_spoilage()
        with perf_timer('Public order'):
            worldwide_public_order(world)
        with perf_timer('Taxes'):
            worldwide_taxes(world)

        with perf_timer('Finalize turn'):
            world.current_turn += 1
            world.save()

            world.broadcast(
                "messaging/messages/new_turn.html",
                'A month goes by...',
                {'world': world}
            )

            world.blocked_for_turn = False
            world.save()
