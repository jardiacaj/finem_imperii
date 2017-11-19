from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from battle.models import BattleFormation
from organization.models import Capability
from organization.views.capabilities_generics import capability_success
from organization.views.decorator import capability_required_decorator


def check_line_formation_validity(request):
    element_size = int(request.POST['line_depth'])
    spacing = int(request.POST['line_spacing'])
    if not 0 < element_size <= 10 or not spacing <= 15:
        raise Http404("Invalid settings")
    return element_size, spacing


def check_column_formation_validity(request):
    element_size = int(request.POST['column_width'])
    spacing = int(request.POST['column_spacing'])
    if not 0 < element_size <= 10 or not spacing <= 15:
        raise Http404("Invalid settings")
    return element_size, spacing


def check_square_wedge_iwedge_formation_validity(request):
    element_size = None
    spacing = int(request.POST['square_spacing'])
    if not spacing <= 15:
        raise Http404("Invalid settings")
    return element_size, spacing


formation_validity_checks = {
    BattleFormation.LINE: check_line_formation_validity,
    BattleFormation.COLUMN: check_column_formation_validity,
    BattleFormation.SQUARE: check_square_wedge_iwedge_formation_validity,
    BattleFormation.WEDGE: check_square_wedge_iwedge_formation_validity,
    BattleFormation.IWEDGE: check_square_wedge_iwedge_formation_validity,
}


@require_POST
@capability_required_decorator
def formation_capability_view(request, capability_id):
    capability = get_object_or_404(
        Capability, id=capability_id, type=Capability.BATTLE_FORMATION)

    new_formation = request.POST['new_formation']
    if new_formation not in formation_validity_checks.keys():
        raise Http404("Invalid formation")
    else:
        element_size, spacing = formation_validity_checks[new_formation](
            request)

    proposal = {
        'formation': new_formation,
        'spacing': spacing,
        'element_size': element_size
    }
    capability.create_proposal(request.hero, proposal)
    return capability_success(capability, request)
