import json

from django.db import models
from django.urls import reverse

import character.models
import organization.models.document
import organization.models.organization
import world.models
from battle.models import BattleFormation
from messaging import shortcuts
from mixins import AdminURLMixin


class Capability(models.Model, AdminURLMixin):
    BAN = 'ban'
    POLICY_DOCUMENT = 'policy'
    CONSCRIPT = 'conscript'
    DIPLOMACY = 'diplomacy'
    HEIR = 'heir'
    ELECT = 'elect'
    CANDIDACY = 'candidacy'
    CONVOKE_ELECTIONS = 'convoke elections'
    MILITARY_STANCE = 'military stance'
    BATTLE_FORMATION = 'battle formation'
    CONQUEST = 'occupy region'
    TAKE_GRAIN = 'take grain'
    GUILDS = 'manage guilds'
    TAXES = 'manage taxation'

    TYPE_CHOICES = (
        (BAN, 'ban'),
        (POLICY_DOCUMENT, 'write policy and law'),
        (DIPLOMACY, 'conduct diplomacy'),
        (CONSCRIPT, 'conscript troops'),
        (HEIR, 'set heir'),
        (ELECT, 'elect'),
        (CANDIDACY, 'present candidacy'),
        (CONVOKE_ELECTIONS, 'convoke elections'),
        (MILITARY_STANCE, 'military orders'),
        (BATTLE_FORMATION, 'battle formation'),
        (CONQUEST, 'occupy region'),
        (TAKE_GRAIN, 'take grain'),
        (GUILDS, 'manage guilds'),
        (TAXES, 'manage taxation'),
    )

    organization = models.ForeignKey('Organization', models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    applying_to = models.ForeignKey(
        'Organization', models.CASCADE, related_name='capabilities_to_this')
    stemming_from = models.ForeignKey(
        'Capability', models.CASCADE,
        null=True, blank=True,
        related_name='transfers'
    )

    def get_absolute_url(self):
        return reverse('organization:capability',
                       kwargs={'capability_id': self.id})

    def create_proposal(self, character, proposal_dict):
        voted_proposal = (
                self.organization.is_position or
                self.organization.decision_taking == organization.models.organization.Organization.DISTRIBUTED
        )
        proposal = CapabilityProposal.objects.create(
            proposing_character=character,
            capability=self,
            proposal_json=json.dumps(proposal_dict),
            vote_end_turn=self.organization.world.current_turn + 2,
            democratic=voted_proposal
        )
        if voted_proposal:
            proposal.execute()
        else:
            proposal.announce_proposal()
            proposal.issue_vote(character, CapabilityVote.YEA)

    def is_passive(self):
        return self.type in (self.CONSCRIPT, self.TAKE_GRAIN,)

    def is_individual_action(self):
        return self.is_passive() or self.type in (self.ELECT, self.CANDIDACY)

    def __str__(self):
        return "{} can {} in {}{}".format(
            self.organization,
            self.get_type_display(),
            self.applying_to,
            "" if self.stemming_from is None else " (delegated by {})".format(
                self.stemming_from
            )
        )


class CapabilityProposal(models.Model):
    proposing_character = models.ForeignKey(
        'character.Character', models.PROTECT)
    capability = models.ForeignKey(Capability, models.CASCADE)
    proposal_json = models.TextField()
    vote_end_turn = models.IntegerField()
    executed = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    democratic = models.BooleanField()

    def announce_proposal(self, extra_context=None):
        context = {'proposal': self}
        if extra_context is not None:
            context = {**context, **extra_context}

        message = shortcuts.create_message(
            template='messaging/messages/proposal.html'.format(
                self.capability.type
            ),
            world=self.capability.organization.world,
            category="proposal",
            template_context=context,
            link=self.get_absolute_url(),
        )
        shortcuts.add_organization_recipient(
            message, self.capability.applying_to)
        shortcuts.add_organization_recipient(
            message, self.capability.organization)

    def announce_execution(self, category, extra_context=None, link=None):
        context = {'proposal': self}
        if extra_context is not None:
            context = {**context, **extra_context}

        message = shortcuts.create_message(
            template='messaging/messages/proposal_execution/{}.html'.format(
                self.capability.type
            ),
            world=self.capability.organization.world,
            category=category,
            template_context=context,
            link=(self.get_absolute_url() if link is None and self.democratic
                  else link),
        )
        shortcuts.add_organization_recipient(
            message, self.capability.applying_to)
        shortcuts.add_organization_recipient(
            message, self.capability.organization)
        return message

    def execute(self):
        proposal = self.get_proposal_json_content()
        applying_to = self.capability.applying_to
        if self.capability.type == Capability.POLICY_DOCUMENT:
            try:
                if proposal['new']:
                    document = organization.models.document.PolicyDocument(
                        organization=applying_to)
                else:
                    document = organization.models.document.PolicyDocument.objects.get(
                        id=proposal['document_id'])

                if proposal['delete']:
                    self.announce_execution(
                        "policy",
                        extra_context={
                            'deleted': True,
                            'document': document
                        }
                    )
                    document.delete()
                else:
                    document.title = proposal.get('title')
                    document.body = proposal.get('body')
                    document.public = proposal.get('public') is not None
                    document.last_modified_turn = self.capability. \
                        organization.world.current_turn
                    document.save()

                    self.announce_execution(
                        "policy",
                        extra_context={
                            'new': proposal['new'],
                            'document': document
                        },
                        link=document.get_absolute_url()
                    )

            except organization.models.document.PolicyDocument.DoesNotExist:
                pass

        elif self.capability.type == Capability.BAN:
            try:
                character_to_ban = character.models.Character.objects.get(
                    id=proposal['character_id']
                )
                applying_to.remove_member(character_to_ban)
                self.announce_execution(
                    'ban',
                    {'banned_character': character_to_ban}
                )
            except character.models.Character.DoesNotExist:
                pass

        elif self.capability.type == Capability.CONVOKE_ELECTIONS:
            if applying_to.current_election is None:
                months_to_election = proposal['months_to_election']
                election = applying_to.convoke_elections(
                    months_to_election)
                self.announce_execution(
                    'elections',
                    {'election': election}
                )

        elif self.capability.type == Capability.DIPLOMACY:
            try:
                target_organization = organization.models.organization.Organization.objects.get(
                    id=proposal['target_organization_id'])
                target_relationship = proposal['target_relationship']
                changing_relationship = applying_to. \
                    get_relationship_to(target_organization)
                reverse_relationship = changing_relationship.reverse_relation()
                action_type = proposal['type']

                if self.democratic:
                    self.announce_execution(
                        'diplomacy',
                        {
                            'action_type': action_type,
                            'target_organization': target_organization,
                            'target_relationship': target_relationship,
                            'changing_relationship': changing_relationship,
                            'reverse_relationship': reverse_relationship,
                            'has_to_be_agreed':
                                changing_relationship.
                                    target_has_to_be_agreed_upon(
                                    target_relationship)
                        }
                    )

                if action_type == 'propose':
                    changing_relationship.desire(target_relationship)
                elif action_type == 'accept':
                    if reverse_relationship.desired_relationship == \
                            target_relationship:
                        changing_relationship.set_relationship(
                            target_relationship)
                elif action_type == 'take back':
                    if changing_relationship.desired_relationship == \
                            target_relationship:
                        changing_relationship.desired_relationship = None
                        changing_relationship.save()
                elif action_type == 'refuse':
                    if reverse_relationship.desired_relationship == \
                            target_relationship:
                        reverse_relationship.desired_relationship = None
                        reverse_relationship.save()

            except organization.models.organization.Organization.DoesNotExist:
                pass

        elif self.capability.type == Capability.MILITARY_STANCE:
            try:
                target_organization = organization.models.organization.Organization.objects.get(
                    id=proposal['target_organization_id'])
                if 'region_id' in proposal.keys():
                    region = world.models.geography.Tile.objects.get(
                        id=proposal['region_id'])
                    target_stance = applying_to. \
                        get_region_stance_to(target_organization, region)
                else:
                    target_stance = applying_to. \
                        get_default_stance_to(target_organization)
                target_stance.stance_type = proposal.get('target_stance')
                target_stance.save()

                self.announce_execution(
                    'military stance',
                    extra_context={
                        'stance': target_stance
                    }
                )

            except (
                    world.models.geography.Tile.DoesNotExist,
                    organization.models.organization.Organization.DoesNotExist
            ):
                pass

        elif self.capability.type == Capability.BATTLE_FORMATION:
            try:
                formation = BattleFormation.objects.get(
                    organization=applying_to, battle=None)
            except BattleFormation.DoesNotExist:
                formation = BattleFormation(
                    organization=applying_to, battle=None)
            formation.formation = proposal['formation']
            formation.spacing = proposal['spacing']
            formation.element_size = proposal['element_size']
            formation.save()

            self.announce_execution(
                'battle formation',
                {'formation': formation}
            )

        elif self.capability.type == Capability.CONQUEST:
            try:
                tile = world.models.geography.Tile.objects.get(
                    id=proposal['tile_id'])
                if proposal['stop']:
                    tile_event = world.models.events.TileEvent.objects.get(
                        tile=tile,
                        organization=applying_to,
                        active=True,
                        type=world.models.events.TileEvent.CONQUEST,
                    )
                    tile_event.end_turn = applying_to. \
                        world.current_turn
                    tile_event.active = False
                    tile_event.save()
                    self.announce_execution(
                        'conquest',
                        {
                            'tile_event': tile_event,
                            'action': 'stop'
                        }
                    )
                else:
                    if tile in applying_to.conquestable_tiles():
                        tile_event = world.models.events.TileEvent.objects. \
                            create(
                            tile=tile,
                            type=world.models.events.TileEvent.CONQUEST,
                            organization=applying_to,
                            counter=0,
                            start_turn=applying_to.world.current_turn,
                            active=True
                        )
                        self.announce_execution(
                            'conquest',
                            {
                                'tile_event': tile_event,
                                'action': 'start'
                            }
                        )

                        tile.world.broadcast(
                            'messaging/messages/conquest_start.html',
                            'conquest',
                            {'tile_event': tile_event},
                            tile.get_absolute_url()
                        )

            except (world.models.geography.Tile.DoesNotExist,
                    world.models.events.TileEvent.DoesNotExist):
                pass

        elif self.capability.type == Capability.GUILDS:
            try:
                settlement = world.models.geography.Settlement.objects.get(
                    id=proposal['settlement_id']
                )
                if (
                        (settlement.tile in
                         applying_to.get_all_controlled_tiles())
                        and
                        (proposal['option'] in
                         [choice[0] for choice in
                          world.models.geography.Settlement
                                  .GUILDS_CHOICES])
                ):
                    settlement.guilds_setting = proposal['option']
                    settlement.save()
                    self.announce_execution(
                        'guilds',
                        {'settlement': settlement}
                    )
            except world.models.geography.Settlement.DoesNotExist:
                pass

        elif self.capability.type == Capability.HEIR:
            try:
                first_heir = character.models.Character.objects.get(
                    id=proposal['first_heir'])
                if (
                        first_heir in applying_to.get_heir_candidates()
                        and first_heir != applying_to.get_position_occupier()
                ):
                    applying_to.heir_first = first_heir
                    applying_to.save()

                    second_heir = None if proposal['second_heir'] == 0 else \
                        character.models.Character.objects.get(
                            id=proposal['second_heir']
                        )
                    if second_heir is None or (
                            second_heir in applying_to.get_heir_candidates()
                            and second_heir != applying_to.get_position_occupier()
                    ):
                        applying_to.heir_second = second_heir
                        applying_to.save()

                    message = self.announce_execution('heir')
                    shortcuts.add_organization_recipient(
                        message,
                        applying_to.get_violence_monopoly()
                    )

            except character.models.Character.DoesNotExist:
                pass

        else:
            raise Exception(
                "Executing unknown capability action_type '{}'"
                    .format(self.capability.type)
            )

        self.executed = True
        self.closed = True
        self.save()

    def get_proposal_json_content(self):
        return json.loads(self.proposal_json)

    def issue_vote(self, character, vote):
        CapabilityVote.objects.create(
            proposal=self,
            voter=character,
            vote=vote
        )
        self.execute_if_enough_votes()
        self.close_if_enough_votes()

    def delete_disallowed_votes(self):
        for vote in self.capabilityvote_set.all():
            if not self.capability.organization.character_is_member(
                    vote.voter):
                vote.delete()

    def execute_if_enough_votes(self):
        self.delete_disallowed_votes()
        possible_votes = self.votes_possible()
        if self.votes_yea().count() > possible_votes / 2:
            self.execute()

    def close_if_enough_votes(self):
        self.delete_disallowed_votes()
        possible_votes = self.votes_possible()
        if self.votes_nay().count() > possible_votes / 2:
            self.closed = True
            self.save()

    def votes_possible(self):
        return self.capability.organization.character_members.count()

    def execute_if_majority(self):
        self.delete_disallowed_votes()
        if self.votes_yea().count() > self.votes_nay().count():
            self.execute()

    def votes_yea(self):
        return self.capabilityvote_set.filter(vote=CapabilityVote.YEA)

    def votes_nay(self):
        return self.capabilityvote_set.filter(vote=CapabilityVote.NAY)

    def votes_invalid(self):
        return self.capabilityvote_set.filter(vote=CapabilityVote.INVALID)

    def get_absolute_url(self):
        return reverse('organization:proposal',
                       kwargs={'proposal_id': self.id})

    def __str__(self):
        return "{} proposal by {}".format(
            self.capability.get_type_display(),
            self.proposing_character
        )


class CapabilityVote(models.Model):
    YEA = 'yea'
    NAY = 'nay'
    INVALID = 'invalid'
    VOTE_CHOICES = (
        (YEA, YEA),
        (NAY, NAY),
        (INVALID, INVALID),
    )

    proposal = models.ForeignKey(CapabilityProposal, models.CASCADE)
    voter = models.ForeignKey('character.Character', models.PROTECT)
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
