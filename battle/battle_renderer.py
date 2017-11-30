from django.utils.html import conditional_escape

from battle.models import Battle
from finem_imperii.app_settings import BATTlE_TICKS_PER_TURN


def render_battle_for_view(battle: Battle):
    organizations = {}
    characters = {}
    units = {}
    contubernia = {}
    for battle_side in battle.battleside_set.all():
        for battle_organization in battle_side.battleorganization_set.all():
            organizations[battle_organization.id] = {
                'z': battle_side.z,
                'name': conditional_escape(
                    battle_organization.organization.name),
                'color': battle_organization.organization.color,
            }
            for battle_character in battle_organization.battlecharacter_set.all():
                characters[battle_character.id] = {
                    'organization_id': battle_organization.id,
                    'name': conditional_escape(
                        battle_character.character.name),
                    'in_turn': {}
                }
                for battle_character_in_turn in battle_character.battlecharacterinturn_set.all():
                    characters[battle_character.id]['in_turn'][battle_character_in_turn.battle_turn.num] = {}

            for battle_unit in battle_organization.battleunit_set.all():
                units[battle_unit.id] = {
                    'character_id': battle_unit.owner_id,
                    'organization_id': battle_unit.battle_organization_id,
                    'name': conditional_escape(battle_unit.name),
                    'type': conditional_escape(battle_unit.type),
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
                            'ammo_remaining': contubernium_in_turn.ammo_remaining,
                            'attack_type': conditional_escape(
                                contubernium_in_turn.attack_type_this_turn),
                            'attack_target':
                                contubernium_in_turn.contubernium_attacked_this_turn.battle_contubernium_id
                                if contubernium_in_turn.contubernium_attacked_this_turn
                                else None,
                            'soldiers': []
                        }

                        for soldier in contubernium_in_turn.battlesoldierinturn_set.all():
                            contubernia[contubernium.id]['in_turn'][
                                contubernium_in_turn.battle_turn.num][
                                'soldiers'].append(
                                {
                                    'wound_status': soldier.wound_status
                                }
                            )

    result = {
        'battle_ticks_per_turn': BATTlE_TICKS_PER_TURN,
        'organizations': organizations,
        'characters': characters,
        'units': units,
        'contubernia': contubernia,
        'turn_count': battle.battleturn_set.count(),
    }
    return result
