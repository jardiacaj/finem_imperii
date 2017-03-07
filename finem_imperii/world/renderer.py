import json

from django.forms.models import model_to_dict


def render_world_for_view(world, json_output=True):
    rendered = [render_tile_for_view(tile) for tile in world.tile_set.all()]
    return json.dumps(rendered) if json_output else rendered


def render_tile_for_view(tile):
    result = model_to_dict(tile)
    result['settlements'] = [render_settlement_for_view(settlement) for settlement in tile.settlement_set.all()]
    return result


def render_settlement_for_view(settlement):
    return model_to_dict(settlement)
