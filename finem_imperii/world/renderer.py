import json

from django.forms.models import model_to_dict


def render_world_for_view(world, json_output=True):
    output = {
        'regions': {},
        'settlements': {},
        'organizations': {},
    }

    for tile in world.tile_set.all():
        output['regions'][tile.id] = render_tile_for_view(tile)

        for settlement in tile.settlement_set.all():
            output['settlements'][settlement.id] = render_settlement_for_view(settlement)

    for organization in world.organization_set.all():
        output['organizations'][organization.id] = render_organization_for_view(organization)

    return json.dumps(output) if json_output else output


def render_tile_for_view(tile):
    result = model_to_dict(tile)
    return result


def render_settlement_for_view(settlement):
    result = model_to_dict(settlement)
    result['absolute_coords'] = settlement.get_absolute_coords()
    result['size_name'] = settlement.size_name()
    return result


def render_organization_for_view(organization):
    return {'color': organization.color}
