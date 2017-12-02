import math

from messaging import shortcuts
from organization.models.organization import Organization
from world.models.buildings import Building
from world.models.geography import World


def worldwide_taxes(world: World):
    for state in world.get_violence_monopolies():
        if not state.has_tax_collection:
            continue

        state.tax_countdown -= 1
        state.save()
        if state.tax_countdown <= 0:
            do_state_taxes(state)
            state.tax_countdown = 6
            state.save()


def do_state_taxes(state: Organization):
    if not state.character_members.exists():
        return

    settlement_input = []
    total_input = 0
    for tile in state.get_all_controlled_tiles():
        for settlement in tile.settlement_set.all():
            t = 0
            for guild in settlement.building_set.filter(
                    type=Building.GUILD):
                cash_produced = guild.field_production_counter * 6
                t += cash_produced
                total_input += cash_produced
                guild.field_production_counter = 0
                guild.save()

            settlement_input.append(
                (settlement, t)
            )

    member_share = math.floor(
        total_input / state.character_members.count()
    )
    for member in state.character_members.all():
        member.cash += member_share
        member.save()

    message = shortcuts.create_message(
        'messaging/messages/tax_collection.html',
        state.world,
        'taxes',
        {
            'organization': state,
            'settlement_input': settlement_input,
            'total_input': total_input,
            'member_share': member_share
        }
    )
    shortcuts.add_organization_recipient(message, state)
