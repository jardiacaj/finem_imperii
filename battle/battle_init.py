import math

from django.db import transaction
from django.db.models.aggregates import Avg

from battle.models import BattleFormation, BattleUnit, BattleContubernium, BattleSoldier, BattleOrganization, \
    BattleSide, BattleCharacter, Coordinates, BattleTurn, BattleCharacterInTurn, BattleUnitInTurn, \
    BattleContuberniumInTurn, BattleSoldierInTurn, OrderListElement


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


@transaction.atomic
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
                battle_side=battle_organization.side,
                name=unit.name,
                type=unit.type
            )
            order = unit.default_battle_orders
            order.pk = None
            order.save()
            OrderListElement.objects.create(order=order, battle_unit=battle_unit, position=0)


def initialize_side_positioning(side: BattleSide):
    formation_settings = side.get_formation()
    if formation_settings.formation == BattleFormation.LINE:
        formation = LineFormation(side, formation_settings)
    else:
        raise Exception("Formation {} not known".format(formation_settings.formation))
    formation.make_formation()

    for coords, contub in formation.output_formation():
        contub.x_offset_to_formation = coords.x
        contub.z_offset_to_formation = coords.z
        contub.starting_x_pos = coords.x if side.z else -coords.x
        contub.starting_z_pos = coords.z + 10 if side.z else -coords.z - 10
        contub.save()

    for unit in side.battleunit_set.all()\
            .annotate(avg_x=Avg('battlecontubernium__starting_x_pos'))\
            .annotate(avg_z=Avg('battlecontubernium__starting_z_pos')):
        unit.starting_x_pos = math.floor(unit.avg_x)
        unit.starting_z_pos = math.floor(unit.avg_z)
        unit.save()

        for contub in unit.battlecontubernium_set.all():
            contub.x_offset_to_unit = contub.starting_x_pos - unit.starting_x_pos
            contub.z_offset_to_unit = contub.starting_z_pos - unit.starting_z_pos
            contub.save()


class Line:
    def __init__(self, depth):
        self.depth = depth
        self.columns = []

    def push_contubernium_on_right_side(self, contubernium):
        if not self.columns:
            self.columns.append([contubernium])
        elif len(self.columns[-1]) >= self.depth:
            self.columns.append([contubernium])
        else:
            self.columns[-1].append(contubernium)

    def push_contubernium_on_left_side(self, contubernium):
        if not self.columns:
            self.columns.append([contubernium])
        elif len(self.columns[0]) >= self.depth:
            self.columns.insert(0, [contubernium])
        else:
            self.columns[0].append(contubernium)

    def push_contubernium(self, contubernium, side):
        if side < 0:
            self.push_contubernium_on_left_side(contubernium)
        else:
            self.push_contubernium_on_right_side(contubernium)

    def push_unit(self, unit, side):
        for contubernium in unit.battlecontubernium_set.all():
            self.push_contubernium(contubernium, side)

    @property
    def width(self):
        return len(self.columns)


class LineFormation:
    def __init__(self, battle_side, formation_object):
        self.formation_object = formation_object
        self.battle_side = battle_side
        self.lines = [
            Line(formation_object.element_size),
            Line(formation_object.element_size),
            Line(formation_object.element_size),
            Line(formation_object.element_size),
            Line(formation_object.element_size),
        ]

    def make_formation(self):
        for line_index in range(5):
            for side_index in [0, 1, -1, 2, -2, 3, -3]:
                units = BattleUnit.objects.filter(
                    battle_side=self.battle_side,
                    world_unit__battle_line=line_index,
                    world_unit__battle_side_pos=side_index
                )
                for unit in units:
                    self.lines[line_index].push_unit(unit, side_index)
        #TODO flanks

    def output_formation(self):
        widest_line_width = max([line.width for line in self.lines])
        for line_index, line in enumerate(self.lines):
            for col_index, column in enumerate(line.columns):
                for contub_index, contub in enumerate(column):
                    x = col_index - round(line.width / 2)
                    z = line_index * (self.formation_object.element_size + self.formation_object.spacing) + contub_index
                    yield Coordinates(x, z), contub


def initialize_battle_positioning(battle):
    for side in battle.battleside_set.all():
        initialize_side_positioning(side)


def generate_in_turn_objects(battle):
    turn = BattleTurn.objects.create(
        battle=battle,
        num=0
    )
    for side in battle.battleside_set.all():
        for organization in side.battleorganization_set.all():
            for character in organization.battlecharacter_set.all():
                bcit = BattleCharacterInTurn.objects.create(
                    battle_character=character,
                    battle_turn=turn
                )
                for unit in character.battleunit_set.all():
                    buit = BattleUnitInTurn.objects.create(
                        battle_unit=unit,
                        battle_character_in_turn=bcit,
                        battle_turn=turn,
                        x_pos=unit.starting_x_pos,
                        z_pos=unit.starting_z_pos,
                        order=unit.get_turn_order(),
                    )
                    for contubernium in unit.battlecontubernium_set.all():
                        bcontubit = BattleContuberniumInTurn.objects.create(
                            battle_contubernium=contubernium,
                            battle_unit_in_turn=buit,
                            battle_turn=turn,
                            x_pos=contubernium.starting_x_pos,
                            z_pos=contubernium.starting_z_pos
                        )
                        for soldier in contubernium.battlesoldier_set.all():
                            BattleSoldierInTurn.objects.create(
                                battle_turn=turn,
                                battle_contubernium_in_turn=bcontubit,
                                battle_soldier=soldier
                            )


class BattleAlreadyStartedException(Exception):
    pass


@transaction.atomic
def start_battle(battle):
    if battle.started:
        raise BattleAlreadyStartedException("Battle {} already started!".format(battle.id))

    for unit in battle.get_units_in_battle().all():
        create_contubernia(unit)
    initialize_battle_positioning(battle)
    generate_in_turn_objects(battle)

    battle.started = True
    battle.save()
