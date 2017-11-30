from django.db import models, transaction
from django.utils.html import format_html


class OrganizationRelationship(models.Model):
    class Meta:
        unique_together = (
            ("from_organization", "to_organization"),
        )

    PEACE = 'peace'
    WAR = 'war'
    BANNED = 'banned'
    FRIENDSHIP = 'friendship'
    DEFENSIVE_ALLIANCE = 'defensive alliance'
    ALLIANCE = 'alliance'
    RELATIONSHIP_CHOICES = (
        (PEACE, PEACE),
        (WAR, WAR),
        (BANNED, BANNED),
        (FRIENDSHIP, FRIENDSHIP),
        (DEFENSIVE_ALLIANCE, DEFENSIVE_ALLIANCE),
        (ALLIANCE, ALLIANCE),
    )

    RELATIONSHIP_LEVEL = {
        WAR: 0,
        BANNED: 0,
        PEACE: 1,
        FRIENDSHIP: 2,
        DEFENSIVE_ALLIANCE: 3,
        ALLIANCE: 5
    }

    from_organization = models.ForeignKey(
        'Organization', related_name='relationships_stemming')
    to_organization = models.ForeignKey(
        'Organization', related_name='relationships_receiving')
    relationship = models.CharField(
        max_length=20, choices=RELATIONSHIP_CHOICES, default=PEACE)
    desired_relationship = models.CharField(
        max_length=20, choices=RELATIONSHIP_CHOICES, blank=True, null=True)

    def reverse_relation(self):
        return self.to_organization.get_relationship_to(self.from_organization)

    @staticmethod
    def _get_badge_type(relationship):
        if relationship in (OrganizationRelationship.WAR,
                            OrganizationRelationship.BANNED):
            return 'danger'
        elif relationship == OrganizationRelationship.FRIENDSHIP:
            return 'success'
        elif relationship in (OrganizationRelationship.DEFENSIVE_ALLIANCE,
                              OrganizationRelationship.ALLIANCE):
            return 'info'
        else:
            return 'default'

    @staticmethod
    def _format_relationship(relationship, relationship_name):
        template = '<span class="label label-{badge_type}">{name}</span>'
        return template.format(
            name=relationship_name.capitalize(),
            badge_type=OrganizationRelationship._get_badge_type(relationship)
        )

    def get_relationship_html(self):
        return OrganizationRelationship._format_relationship(
            self.relationship,
            self.get_relationship_display()
        )

    def get_desired_relationship_html(self):
        if self.desired_relationship is None:
            return OrganizationRelationship._format_relationship(
                'default',
                'None'
            )
        else:
            return OrganizationRelationship._format_relationship(
                self.desired_relationship,
                self.get_desired_relationship_display()
            )

    def is_proposal(self):
        return self.desired_relationship and self.desired_relationship != self.relationship

    def target_has_to_be_agreed_upon(self, target_relationship):
        return self.RELATIONSHIP_LEVEL[target_relationship] > self.RELATIONSHIP_LEVEL[self.relationship]

    @transaction.atomic
    def desire(self, target_relationship):
        if self.target_has_to_be_agreed_upon(target_relationship):
            self.desired_relationship = target_relationship
            self.save()
        else:
            self.set_relationship(target_relationship)

    @transaction.atomic
    def set_relationship(self, target_relationship: str):
        previous_relationship = self.relationship
        self.relationship = target_relationship
        self.desired_relationship = None
        self.save()
        reverse_relation = self.reverse_relation()
        reverse_relation.relationship = target_relationship
        reverse_relation.desired_relationship = None
        reverse_relation.save()

        self.to_organization.world.broadcast(
            'messaging/messages/organization_relationship_change.html',
            'diplomacy',
            {
                'relationship': self,
                'previous_relationship': previous_relationship
            }
        )

    def default_military_stance(self):
        if self.relationship in (OrganizationRelationship.PEACE,):
            return MilitaryStance.DEFENSIVE
        if self.relationship in (OrganizationRelationship.WAR,
                                 OrganizationRelationship.BANNED):
            return MilitaryStance.AGGRESSIVE
        return MilitaryStance.AVOID_BATTLE

    def __str__(self):
        return "Relationship {} to {}".format(
            self.from_organization,
            self.to_organization
        )


class MilitaryStance(models.Model):
    class Meta:
        unique_together = (
            ("from_organization", "to_organization", "region"),
        )
    DEFAULT = 'default'
    AVOID_BATTLE = 'avoid battle'
    DEFENSIVE = 'defensive'
    AGGRESSIVE = 'aggressive'

    STANCE_CHOICES=(
        (DEFAULT, "automatic by diplomatic relationship"),
        (AVOID_BATTLE, AVOID_BATTLE),
        (DEFENSIVE, DEFENSIVE),
        (AGGRESSIVE, AGGRESSIVE),
    )

    from_organization = models.ForeignKey(
        'Organization', related_name='mil_stances_stemming')
    to_organization = models.ForeignKey(
        'Organization', related_name='mil_stances_receiving')
    region = models.ForeignKey(
        'world.Tile', related_name='+', null=True, blank=True)
    stance_type = models.CharField(
        max_length=20, choices=STANCE_CHOICES, default=DEFAULT)

    def get_stance(self):
        if self.stance_type != MilitaryStance.DEFAULT:
            return self.stance_type
        if self.region:
            return self.from_organization.get_default_stance_to(
                self.to_organization).get_stance()
        else:
            return self.from_organization.get_relationship_to(
                self.to_organization).default_military_stance()

    def get_html_stance(self):
        stance = self.get_stance()
        if stance == MilitaryStance.DEFENSIVE:
            bootstrap_type = 'primary'
        elif stance == MilitaryStance.AGGRESSIVE:
            bootstrap_type = 'danger'
        elif stance == MilitaryStance.AVOID_BATTLE:
            bootstrap_type = 'info'
        else:
            bootstrap_type = 'default'

        return format_html(
            '<span class="label label-{bootstrap_type}">{stance}</span>',
           bootstrap_type=bootstrap_type,
           stance=stance
       )
