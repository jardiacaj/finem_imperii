import json
from numbers import Number

from django.forms.models import model_to_dict
from django.utils.html import conditional_escape

from organization.models.organization import Organization
from world.models.geography import Tile, Settlement, World


def render_world_for_view(world: World, json_output=True):
    output = {
        'regions': {},
        'settlements': {},
        'organizations': {},
    }

    for tile in world.tile_set.all():
        output['regions'][tile.id] = render_tile_for_view(tile)

        for settlement in tile.settlement_set.all():
            settlement_for_view = render_settlement_for_view(settlement)
            output['settlements'][settlement.id] = settlement_for_view

    for organization in world.organization_set.all():
        organization_for_view = render_organization_for_view(organization)
        output['organizations'][organization.id] = organization_for_view

    return json.dumps(output) if json_output else output


def escape_all_non_number_dict_elements(input_dict):
    return {
        k if isinstance(k, Number) else conditional_escape(k):
        v if isinstance(v, Number) else conditional_escape(v)
        for k, v in input_dict.items()
    }


def render_tile_for_view(tile: Tile):
    result = model_to_dict(tile)
    return escape_all_non_number_dict_elements(result)


def render_settlement_for_view(settlement: Settlement):
    result = model_to_dict(settlement)
    escaped_result = escape_all_non_number_dict_elements(result)
    escaped_result['absolute_coords'] = settlement.get_absolute_coords()
    return escaped_result


def render_organization_for_view(organization: Organization):
    result = {'color': organization.color}
    return escape_all_non_number_dict_elements(result)
