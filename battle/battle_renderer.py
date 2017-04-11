from battle.models import Battle


def render_battle_for_view(battle: Battle):
    organizations = {}
    characters = {}
    units = {}
    contubernia = {}
    for battle_side in battle.battleside_set.all():
        for battle_organization in battle_side.battleorganization_set.all():
            organizations[battle_organization.id] = {
                'z': battle_side.z,
                'name': battle_organization.organization.name,
            }
            for battle_character in battle_organization.battlecharacter_set.all():
                characters[battle_character.id] = {
                    'organization_id': battle_organization.id,
                    'name': battle_character.character.name,
                    'in_turn': {}
                }
                for battle_character_in_turn in battle_character.battlecharacterinturn_set.all():
                    characters[battle_character.id]['in_turn'][battle_character_in_turn.battle_turn.num] = {}

                for battle_unit in battle_character.battleunit_set.all():
                    units[battle_unit.id] = {
                        'character_id': battle_character.id,
                        'name': battle_unit.name,
                        'type': battle_unit.type,
                        'in_turn': {}
                    }
                    for battle_unit_in_turn in battle_unit.battleunitinturn_set.all():
                        units[battle_unit.id]['in_turn'][battle_unit_in_turn.battle_turn.num] = {
                            'x_pos': battle_unit_in_turn.x_pos,
                            'z_pos': battle_unit_in_turn.z_pos,
                        }

                    for contubernium in battle_unit.battlecontubernium_set.all():
                        contubernia[contubernium.id] = {
                            'unit_id': battle_unit.id,
                            'in_turn': {}
                        }

                        for contubernium_in_turn in contubernium.battlecontuberniuminturn_set.all():
                            contubernia[contubernium.id]['in_turn'][contubernium_in_turn.battle_turn.num] = {
                                'x_pos': contubernium_in_turn.x_pos,
                                'z_pos': contubernium_in_turn.z_pos,
                            }

    result = {
        'organizations': organizations,
        'characters': characters,
        'units': units,
        'contubernia': contubernia,
        'turn_count': battle.battleturn_set.count(),
    }
    return result
