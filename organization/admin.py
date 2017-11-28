from django.contrib import admin

from organization.models.relationship import OrganizationRelationship, \
    MilitaryStance
from organization.models.document import PolicyDocument
from organization.models.capability import Capability, CapabilityProposal, \
    CapabilityVote
from organization.models.election import PositionElection, PositionCandidacy, \
    PositionElectionVote
from organization.models.organization import Organization

admin.site.register(PositionElection)
admin.site.register(PositionCandidacy)
admin.site.register(PositionElectionVote)
admin.site.register(Capability)
admin.site.register(CapabilityProposal)
admin.site.register(CapabilityVote)
admin.site.register(PolicyDocument)
admin.site.register(OrganizationRelationship)
admin.site.register(MilitaryStance)


def resolve_organization_election(modeladmin, request, queryset):
    for organization in queryset.all():
        if organization.current_election:
            organization.current_election.resolve()
resolve_organization_election.short_description = "Resolve current election"


@admin.register(Organization)
class WorldAdmin(admin.ModelAdmin):
    actions = [resolve_organization_election, ]