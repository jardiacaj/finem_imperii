import math

from django.db import transaction
from django.db.models.aggregates import Avg

from battle.models import BattleFormation, BattleUnit, BattleContubernium, \
    BattleSoldier, BattleOrganization, \
    BattleSide, BattleCharacter, Coordinates, BattleTurn, \
    BattleCharacterInTurn, BattleUnitInTurn, \
    BattleContuberniumInTurn, BattleSoldierInTurn, Battle
from unit.models import WorldUnit


def create_contubernia(unit: BattleUnit):
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
            BattleSoldier.objects.create(
                battle_contubernium=contubernium,
                world_npc=soldier
            )
        pointer = end


@transaction.atomic
def initialize_from_conflict(battle, conflict, tile):
    for i, conflict_side in enumerate(conflict):
        battle_side = BattleSide.objects.create(
            battle=battle,
            z=i
        )
        for organization in conflict_side:
            BattleOrganization.objects.create(
                side=battle_side,
                organization=organization
            )
    conflicting_states = conflict[0] + conflict[1]
    for unit in tile.get_units():
        violence_monopoly = unit.get_violence_monopoly()
        if violence_monopoly in conflicting_states:
            battle_organization = BattleOrganization.objects.get(
                side__battle=battle,
                organization=violence_monopoly
            )
            if unit.owner_character:
                battle_character = BattleCharacter.objects.get_or_create(
                    battle_organization=battle_organization,
                    character=unit.owner_character,
                    present_in_battle=(
                        unit.owner_character.location.tile == unit.location.tile
                    )
                )[0]
            else:
                battle_character = None
            battle_unit = BattleUnit.objects.create(
                battle_organization=battle_organization,
                owner=battle_character,
                world_unit=unit,
                starting_manpower=unit.get_fighting_soldiers().count(),
                battle_side=battle_organization.side,
                name=unit.name,
                type=unit.type
            )


def initialize_side_positioning(side: BattleSide):
    formation_settings = side.get_formation()
    if formation_settings.formation == BattleFormation.LINE:
        formation = LineFormation(side, formation_settings)
    else:
        raise Exception(
            "Formation {} not known".format(formation_settings.formation)
        )
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

        set_contubernia_starting_pos(unit)


def set_contubernia_starting_pos(unit: BattleUnit):
    for contub in unit.battlecontubernium_set.all():
        contub.x_offset_to_unit = contub.starting_x_pos - \
                                  unit.starting_x_pos
        contub.z_offset_to_unit = contub.starting_z_pos - \
                                  unit.starting_z_pos
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
        self.main_lines = [
            self.new_line(), self.new_line(), self.new_line(),
            self.new_line(), self.new_line(),
        ]
        self.flanks = [
            [self.new_line(), self.new_line(), self.new_line(),
             self.new_line(), self.new_line(), ],
            [self.new_line(), self.new_line(), self.new_line(),
             self.new_line(), self.new_line(), ],
        ]
        self.far_flanks = [
            [self.new_line(), self.new_line(), self.new_line(),
             self.new_line(), self.new_line(), ],
            [self.new_line(), self.new_line(), self.new_line(),
             self.new_line(), self.new_line(), ],
        ]

    def new_line(self):
        return Line(self.formation_object.element_size)

    def make_formation(self):
        for line_index in range(5):
            for side_index in [0, 1, -1, 2, -2, 3, -3]:
                units = self.get_battle_units_by_battle_settings(
                    line_index, side_index
                )
                for unit in units:
                    self.main_lines[line_index].push_unit(unit, side_index)

            for side_index in [-4, 4]:
                far_flank_index = 0 if side_index < 0 else 1
                units = self.get_battle_units_by_battle_settings(
                    line_index, side_index
                )
                for unit in units:
                    self.flanks[far_flank_index][line_index].push_unit(unit, 0)

            for side_index in [-5, 5]:
                far_flank_index = 0 if side_index < 0 else 1
                units = self.get_battle_units_by_battle_settings(
                    line_index, side_index
                )
                for unit in units:
                    self.far_flanks[far_flank_index][line_index].push_unit(
                        unit, 0
                    )

    def get_battle_units_by_battle_settings(self, line_index, side_index):
        return BattleUnit.objects.filter(
            battle_side=self.battle_side,
            world_unit__battle_line=line_index,
            world_unit__battle_side_pos=side_index
        )

    def output_formation(self):
        widest_main_line_width = max([line.width for line in self.main_lines])
        full_size_of_line = (self.formation_object.element_size +
                             self.formation_object.spacing)
        flanks_x_offset = round(widest_main_line_width / 2) + \
                                self.formation_object.spacing
        min_x = 0
        max_x = 0

        for line_index, line in enumerate(self.main_lines):
            for col_index, column in enumerate(line.columns):
                for contub_index, contub in enumerate(column):
                    x = col_index - round(line.width / 2)
                    z = line_index * full_size_of_line + contub_index
                    yield Coordinates(x, z), contub

        for flank_index, flank in enumerate(self.flanks):
            x_multiplier = -1 if flank_index == 0 else 1
            x_offset = flanks_x_offset * x_multiplier
            for line_index, line in enumerate(flank):
                for col_index, column in enumerate(line.columns):
                    for contub_index, contub in enumerate(column):
                        x = x_offset + col_index * x_multiplier
                        z = line_index * full_size_of_line + contub_index
                        min_x = min(x, min_x)
                        max_x = max(x, max_x)
                        yield Coordinates(x, z), contub

        for far_flank_index, far_flank in enumerate(self.far_flanks):
            if far_flank_index == 0:
                x_multiplier = -1
                x_offset = min_x - self.formation_object.spacing * 2
            else:
                x_multiplier = 1
                x_offset = max_x + self.formation_object.spacing * 2
            for line_index, line in enumerate(far_flank):
                for col_index, column in enumerate(line.columns):
                    for contub_index, contub in enumerate(column):
                        x = x_offset + col_index * x_multiplier
                        z = line_index * full_size_of_line + contub_index
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
            for unit in organization.battleunit_set.all():
                generate_in_turn_objects_for_unit(turn, unit)
    for barbarian_unit in BattleUnitInTurn.objects.filter(
        battle_unit__owner=None,
        battle_turn=turn
    ):
        barbarian_unit.order = barbarian_unit.battle_unit.get_order()
        barbarian_unit.save()


def generate_in_turn_objects_for_unit(turn: BattleTurn, unit: BattleUnit):
    if unit.world_unit.owner_character:
        owner_in_turn = BattleCharacterInTurn.objects.get(
            battle_character=unit.owner,
            battle_turn=turn
        )
    else:
        owner_in_turn = None
    buit = BattleUnitInTurn.objects.create(
        battle_unit=unit,
        battle_character_in_turn=owner_in_turn,
        battle_turn=turn,
        x_pos=unit.starting_x_pos,
        z_pos=unit.starting_z_pos,
        order=unit.get_order()
    )
    for contubernium in unit.battlecontubernium_set.all():
        bcontubit = BattleContuberniumInTurn.objects.create(
            battle_contubernium=contubernium,
            battle_unit_in_turn=buit,
            battle_turn=turn,
            x_pos=contubernium.starting_x_pos,
            z_pos=contubernium.starting_z_pos,
            ammo_remaining=unit.world_unit.starting_ammo()
        )
        for soldier in contubernium.battlesoldier_set.all():
            BattleSoldierInTurn.objects.create(
                battle_turn=turn,
                battle_contubernium_in_turn=bcontubit,
                battle_soldier=soldier
            )


def joining_contubernium_position_generator():
    for z in range(30, 48):
        for x in range(20):
            for multiplier in (-1, 1):
                yield Coordinates(x=x*multiplier, z=z)


def add_unit_to_battle_in_progress(
        battle_organization: BattleOrganization,
        world_unit: WorldUnit
):
    battle = battle_organization.side.battle
    if world_unit.owner_character:
        battle_character = BattleCharacter.objects.get_or_create(
            battle_organization=battle_organization,
            character=world_unit.owner_character,
            present_in_battle=(
                world_unit.owner_character.location.tile == world_unit.location.tile
            )
        )[0]
        battle_character_in_turn = BattleCharacterInTurn.objects.get_or_create(
            battle_character=battle_character,
            battle_turn=battle.get_latest_turn()
        )
    else:
        battle_character = None
    battle_unit = BattleUnit.objects.create(
        battle_organization=battle_organization,
        owner=battle_character,
        world_unit=world_unit,
        starting_manpower=world_unit.get_fighting_soldiers().count(),
        battle_side=battle_organization.side,
        name=world_unit.name,
        type=world_unit.type
    )
    create_contubernia(battle_unit)

    position_generator = joining_contubernium_position_generator()

    for contub in battle_unit.battlecontubernium_set.all():
        coords = next(position_generator)
        while battle.get_latest_turn().get_contubernium_in_position(coords) is not None:
            coords = next(position_generator)

        contub.x_offset_to_formation = coords.x
        contub.z_offset_to_formation = coords.z
        contub.starting_x_pos = coords.x if battle_organization.side.z else -coords.x
        contub.starting_z_pos = coords.z + 10 if battle_organization.side.z else -coords.z - 10
        contub.save()

    battle_unit.starting_x_pos = math.floor(battle_unit.battlecontubernium_set.all().aggregate(Avg('starting_x_pos'))['starting_x_pos__avg'])
    battle_unit.starting_z_pos = math.floor(battle_unit.battlecontubernium_set.all().aggregate(Avg('starting_z_pos'))['starting_z_pos__avg'])
    battle_unit.save()

    set_contubernia_starting_pos(battle_unit)


class BattleAlreadyStartedException(Exception):
    pass


@transaction.atomic
def start_battle(battle: Battle):
    if battle.started:
        raise BattleAlreadyStartedException(
            "Battle {} already started!".format(battle.id)
        )

    for unit in battle.get_units_in_battle().all():
        create_contubernia(unit)
    initialize_battle_positioning(battle)
    generate_in_turn_objects(battle)

    battle.started = True
    battle.save()
