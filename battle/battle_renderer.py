def render_battle_for_view(battle):
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
                }
                for battle_unit in battle_character.battleunit_set.all():
                    units[battle_unit.id] = {
                        'character_id': battle_character.id,
                        'name': battle_unit.name,
                        'type': battle_unit.type
                    }
                    for contubernium in battle_unit.battlecontubernium_set.all():
                        contubernia[contubernium.id] = {
                            'unit_id': battle_unit.id,
                        }

    result = {
        'organizations': organizations,
        'characters': characters,
        'units': units,
        'contubernia': contubernia
    }
    return result
