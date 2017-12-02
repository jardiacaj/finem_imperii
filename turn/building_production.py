from world.models.buildings import Building
from world.models.geography import World

field_input_months = (0, 1, 2, 3, 4, 5, 8, 9, 10, 11)
field_output_months = (4, 5, 6, 7, 8)
field_output_multipliers = {4: 0.5, 5: 1, 6: 0.5, 7: 1, 8: 0.5}
field_production_reset_month = 8


def worldwide_building_production(world: World):
    for building in Building.objects.filter(
            settlement__tile__world=world):
        do_building_production(building)


def do_building_production(building: Building):
    workers = building.worker
    ideal_workers = min(building.max_ideal_workers(), workers.count())
    surplus_workers = max(
        0,
        workers.count() - building.max_ideal_workers()
    )

    work_input = 0
    if building.max_ideal_workers():
        work_input += min(
            (ideal_workers / building.max_ideal_workers()),
            1)
    if building.max_surplus_workers():
        work_input += min(
            (surplus_workers / building.max_surplus_workers()) * 0.5,
            0.5)

    if building.type == Building.GRAIN_FIELD and building.level > 0:
        current_month = building.settlement.tile.world.current_turn % 12

        if current_month in field_output_months and work_input > 0:
            time_portion = \
                field_output_multipliers[current_month] / \
                sum(field_output_multipliers.values())
            production_counter_remove = min(
                work_input * time_portion * 1000,
                building.field_production_counter
            )
            building.field_production_counter -= production_counter_remove
            building.save()
            bushel_output = (
                building.quantity
                * production_counter_remove / 1000
                * 2.4
            )
            building.settlement.get_default_granary().add_bushels(
                round(bushel_output)
            )

        if current_month == field_production_reset_month:
            building.field_production_counter = 0
            building.save()

        if current_month in field_input_months and work_input > 0:
            time_portion = 1 / len(field_input_months)
            production_counter_add = work_input * time_portion * 1000
            building.field_production_counter += production_counter_add
            building.save()

    if building.type == Building.GUILD:
        building.field_production_counter *= 0.9
        building.field_production_counter += workers.count()
        building.save()
