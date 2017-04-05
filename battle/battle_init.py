import math

from battle.models import BattleFormation, BattleUnit, BattleContubernium, BattleSoldier, BattleOrganization, \
    BattleSide, BattleCharacter


def create_contubernia(unit):
    soldiers = unit.world_unit.get_fighting_soldiers()
    num_contubernia = math.ceil(soldiers.count() / 8)
    rest = soldiers.count() % 8
    pointer = 0
    for i in range(num_contubernia):
        start = pointer
        end = pointer + (8 if i < rest else 7)
        contubernium_soldiers = soldiers[start:end]
        contubernium = BattleContubernium.objects.create(battle_unit=unit)
        for soldier in contubernium_soldiers:
            BattleSoldier.objects.create(battle_contubernium=contubernium, world_npc=soldier)
        pointer = end


def initialize_from_conflict(battle, conflict, tile):
    z = False
    for organization in conflict:
        battle_side = BattleSide.objects.create(battle=battle, z=z)
        BattleOrganization.objects.create(side=battle_side, organization=organization)
        z = True
    for unit in tile.get_units():
        violence_monopoly = unit.owner_character.get_violence_monopoly()
        if violence_monopoly in conflict:
            battle_organization = BattleOrganization.objects.get(side__battle=battle, organization=violence_monopoly)
            battle_character = BattleCharacter.objects.get_or_create(
                battle_organization=battle_organization,
                character=unit.owner_character,
            )[0]
            battle_unit = BattleUnit.objects.create(
                owner=battle_character,
                world_unit=unit,
                starting_manpower=unit.get_fighting_soldiers().count(),
                battle_side=battle_organization.side
            )


def initialize_side_positioning(side):
    formation = side.get_formation()
    if formation == BattleFormation.LINE:
        formation = LineFormation(side)
    else:
        raise Exception("Formation {} not known".format(formation))
    formation.make_formation()


class LineFormation:
    class Flank:
        pass

    class Line:
        pass

    def __init__(self, side):
        self.side = side
        self.lines = [
            LineFormation.Line(),
            LineFormation.Line(),
            LineFormation.Line(),
            LineFormation.Line(),
            LineFormation.Line(),
        ]
        self.near_flanks = [LineFormation.Line(), LineFormation.Line()]
        self.far_flanks = [LineFormation.Line(), LineFormation.Line()]

    def make_formation(self):
        for line_index in range(5):
            units = BattleUnit.objects.filter(battle_side=self.side, world_unit__battle_line=line_index)
            center_units = units.filter(world_unit__battle_side_pos=0)


def initialize_battle_positioning(battle):
    for side in battle.battleside_set.all():
        initialize_side_positioning(side)


def start_battle(battle):
    for unit in battle.get_units_in_battle().all():
        create_contubernia(unit)
    initialize_battle_positioning(battle)
