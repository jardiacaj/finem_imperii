from django.db import models, transaction
from django.db.models import Count
from django.urls import reverse

import world.templatetags
from messaging import shortcuts


class PositionElection(models.Model):
    position = models.ForeignKey('Organization', models.CASCADE)
    turn = models.IntegerField()
    closed = models.BooleanField(default=False)
    winner = models.ForeignKey('PositionCandidacy', models.SET_NULL,
                               blank=True, null=True)

    def open_candidacies(self):
        return self.positioncandidacy_set.filter(retired=False)

    def last_turn_to_present_candidacy(self):
        return self.turn - 3

    def can_present_candidacy(self):
        return self.position.world.current_turn <= \
               self.last_turn_to_present_candidacy()

    @transaction.atomic
    def resolve(self):
        max_votes = 0
        winners = []
        for candidacy in self.open_candidacies().all():
            votes = candidacy.positionelectionvote_set.count()
            if votes > max_votes:
                max_votes = votes
                winners = []
            if votes == max_votes:
                winners.append(candidacy)

        if len(winners) != 1:
            self.position.convoke_elections()
            winning_candidate = None
        else:
            winning_candidacy = winners[0]
            winning_candidate = winning_candidacy.candidate
            self.winner = winning_candidacy
            self.position.character_members.remove(
                self.position.get_position_occupier())
            self.position.character_members.add(winning_candidate)

        message = shortcuts.create_message(
            'messaging/messages/elections_resolved.html',
            self.position.world,
            'elections',
            {
                'election': self,
                'winner_count': len(winners),
                'winner': winning_candidate
            },
            link=self.get_absolute_url()
        )
        shortcuts.add_organization_recipient(
            message,
            self.position,
            add_lead_organizations=True
        )

        self.position.last_election = self
        self.position.current_election = None
        self.position.save()
        self.closed = True
        self.save()

    def get_results(self):
        return self.positioncandidacy_set.all().annotate(
            num_votes=Count('positionelectionvote')) \
            .order_by('-num_votes')

    def get_absolute_url(self):
        return reverse(
            'organization:election',
            kwargs={'election_id': self.id}
        )

    def __str__(self):
        return "{} election for {}".format(
            world.templatetags.extra_filters.nice_turn(self.turn),
            self.position
        )


class PositionCandidacy(models.Model):
    class Meta:
        unique_together = (
            ("election", "candidate"),
        )

    election = models.ForeignKey(PositionElection, models.CASCADE)
    candidate = models.ForeignKey('character.Character', models.PROTECT)
    description = models.TextField()
    retired = models.BooleanField(default=False)


class PositionElectionVote(models.Model):
    class Meta:
        unique_together = (
            ("election", "voter"),
        )

    election = models.ForeignKey(PositionElection, models.CASCADE)
    voter = models.ForeignKey('character.Character', models.PROTECT)
    candidacy = models.ForeignKey(PositionCandidacy, models.CASCADE,
                                  blank=True, null=True)
