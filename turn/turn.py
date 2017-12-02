from turn.barbarians import worldwide_barbarian_generation
from turn.battle import worldwide_trigger_battles, worldwide_battle_joins, \
    worldwide_battle_starts, worldwide_battle_turns
from turn.building_production import worldwide_building_production
from turn.character import worldwide_pause_characters, \
    worldwide_character_travels, \
    worldwide_restore_character_hours
from turn.conquest import worldwide_do_conquests
from turn.demography import worldwide_food_consumption, \
    worldwide_population_changes
from turn.elections import worldwide_do_elections
from turn.npc_jobs import worldwide_npc_job_updates
from turn.public_order import worldwide_public_order_update
from turn.taxes import worldwide_taxes
from turn.unit import worldwide_unit_maintenance


def pass_turn(world):
    world.blocked_for_turn = True
    world.save()

    # worldwide_delete_dead_realms()
    worldwide_pause_characters(world)
    worldwide_character_travels(world)
    worldwide_restore_character_hours(world)
    worldwide_unit_maintenance(world)
    worldwide_battle_starts(world)
    worldwide_battle_joins(world)
    worldwide_battle_turns(world)
    worldwide_trigger_battles(world)
    worldwide_do_elections(world)
    worldwide_do_conquests(world)
    worldwide_barbarian_generation(world)
    # worldwide_do_residence_assignment()
    worldwide_npc_job_updates(world)
    worldwide_building_production(world)
    # worldiwde_to_trade()
    worldwide_food_consumption(world)
    worldwide_population_changes(world)
    # worldwide_food_spoilage()
    worldwide_public_order_update(world)
    worldwide_taxes(world)

    world.current_turn += 1
    world.save()

    world.broadcast(
        "messaging/messages/new_turn.html",
        'turn',
        {'world': world}
    )

    world.blocked_for_turn = False
    world.save()
