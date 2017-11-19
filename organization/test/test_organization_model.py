from django.test import TestCase

from organization.models import Organization, Capability, OrganizationRelationship, PositionElection, PositionCandidacy, \
    MilitaryStance
from world.models import Tile
from character.models import Character


class TestOrganizationModel(TestCase):
    fixtures = ["simple_world"]

    def test_get_descendants_excluding_self(self):
        kingdom = Organization.objects.get(name="Small Kingdom")
        descendants = kingdom.get_descendants_list()
        self.assertEqual(len(descendants), 3)
        self.assertIn(Organization.objects.get(name="Governor of some forest"), descendants)
        self.assertIn(Organization.objects.get(name="Governor of some plains"), descendants)
        self.assertIn(Organization.objects.get(name="Helper of the governor of some plains"), descendants)

    def test_get_descendants_including_self(self):
        kingdom = Organization.objects.get(name="Governor of some plains")
        descendants = kingdom.get_descendants_list(including_self=True)
        self.assertEqual(len(descendants), 2)
        self.assertIn(Organization.objects.get(name="Governor of some plains"), descendants)
        self.assertIn(Organization.objects.get(name="Helper of the governor of some plains"), descendants)

    def test_get_membership_including_descendants(self):
        kingdom = Organization.objects.get(name="Governor of some plains")
        membership = kingdom.get_membership_including_descendants()
        self.assertEqual(len(membership), 1)
        self.assertIn(Character.objects.get(id=2), membership)

    def test_get_membership_including_descendants2(self):
        kingdom = Organization.objects.get(name="Small Kingdom")
        membership = kingdom.get_membership_including_descendants()
        self.assertEqual(len(membership), 2)
        self.assertIn(Character.objects.get(id=1), membership)
        self.assertIn(Character.objects.get(id=2), membership)

    def test_organizations_character_can_apply_capabilities_to_this_with(self):
        king = Character.objects.get(id=1)
        king_position = Organization.objects.get(name="Small King")
        kingdom = Organization.objects.get(name="Small Kingdom")

        result = kingdom.organizations_character_can_apply_capabilities_to_this_with(king, Capability.BAN)
        self.assertEqual(len(result), 1)
        self.assertIn(king_position, result)

    def test_organizations_character_can_apply_capabilities_to_this_with2(self):
        king = Character.objects.get(id=2)
        kingdom = Organization.objects.get(name="Small Kingdom")

        result = kingdom.organizations_character_can_apply_capabilities_to_this_with(king, Capability.BAN)
        self.assertEqual(len(result), 0)

    def test_organizations_character_can_apply_capabilities_to_this_with3(self):
        king = Character.objects.get(id=1)
        king_position = Organization.objects.get(name="Small King")
        kingdom = Organization.objects.get(name="Small Kingdom")

        result = kingdom.organizations_character_can_apply_capabilities_to_this_with(king, Capability.CONSCRIPT)
        self.assertEqual(len(result), 2)
        self.assertIn(king_position, result)
        self.assertIn(kingdom, result)

    def test_character_is_member(self):
        king = Character.objects.get(id=1)
        other_guy = Character.objects.get(id=2)
        kingdom = Organization.objects.get(name="Small Kingdom")

        self.assertTrue(kingdom.character_is_member(king))
        self.assertTrue(kingdom.character_is_member(other_guy))

    def test_is_part_of_violence_monopoly(self):
        organization = Organization.objects.get(name="Small Kingdom")
        self.assertEqual(organization.get_violence_monopoly(), organization)

    def test_is_part_of_violence_monopoly2(self):
        organization = Organization.objects.get(name="Small King")
        result = Organization.objects.get(name="Small Kingdom")
        self.assertEqual(organization.get_violence_monopoly(), result)

    def test_is_part_of_violence_monopoly3(self):
        organization = Organization.objects.get(name="Governor of some plains")
        result = Organization.objects.get(name="Small Kingdom")
        self.assertEqual(organization.get_violence_monopoly(), result)

    def test_is_part_of_violence_monopoly4(self):
        organization = Organization.objects.get(name="Helper of the governor of some plains")
        result = Organization.objects.get(name="Small Kingdom")
        self.assertEqual(organization.get_violence_monopoly(), result)

    def test_is_part_of_violence_monopoly5(self):
        organization = Organization.objects.get(name="Small Federation")
        self.assertIsNone(organization.get_violence_monopoly())

    def test_is_part_of_violence_monopoly6(self):
        organization = Organization.objects.get(name="President of the Small Federation")
        self.assertIsNone(organization.get_violence_monopoly())

    def test_is_part_of_violence_monopoly7(self):
        organization = Organization.objects.get(name="Horde")
        self.assertEqual(organization.get_violence_monopoly(), organization)

    def test_get_all_controlled_tiles(self):
        organization = Organization.objects.get(name="Small Kingdom")
        controlled_tiles = organization.get_all_controlled_tiles()
        self.assertEqual(len(controlled_tiles), 2)
        self.assertIn(Tile.objects.get(name="Some plains"), controlled_tiles)
        self.assertIn(Tile.objects.get(name="Some forest"), controlled_tiles)

    def test_get_all_controlled_tiles2(self):
        organization = Organization.objects.get(name="Governor of some plains")
        controlled_tiles = organization.get_all_controlled_tiles()
        self.assertEqual(len(controlled_tiles), 1)
        self.assertIn(Tile.objects.get(name="Some plains"), controlled_tiles)

    def test_get_all_controlled_tiles3(self):
        organization = Organization.objects.get(name="Helper of the governor of some plains")
        controlled_tiles = organization.get_all_controlled_tiles()
        self.assertEqual(len(controlled_tiles), 0)

    def test_external_capabilities_to_this(self):
        organization = Organization.objects.get(name="Small King")
        external_capabilities = organization.external_capabilities_to_this()
        self.assertEqual(len(external_capabilities), 0)

    def test_external_capabilities_to_this2(self):
        organization = Organization.objects.get(name="Small Kingdom")
        external_capabilities = organization.external_capabilities_to_this()
        self.assertEqual(len(external_capabilities), 10)
        self.assertTrue(external_capabilities.filter(type=Capability.BAN, organization__name="Small King").exists())

    def test_get_position_occupier(self):
        organization = Organization.objects.get(name="Small King")
        self.assertEqual(organization.get_position_occupier().id, 1)

    def test_get_position_occupier2(self):
        organization = Organization.objects.get(name="Small Kingdom")
        self.assertEqual(organization.get_position_occupier(), None)

    def test_get_relationship_to(self):
        organization1 = Organization.objects.get(name="Small Kingdom")
        organization2 = Organization.objects.get(name="Small Commonwealth")
        self.assertEqual(organization1.get_relationship_to(organization2).relationship, OrganizationRelationship.PEACE)

    def test_get_relationship_from(self):
        organization1 = Organization.objects.get(name="Small Kingdom")
        organization2 = Organization.objects.get(name="Small King")
        self.assertEqual(organization1.get_relationship_from(organization2).relationship, OrganizationRelationship.PEACE)

    def test_get_war_relationship_to(self):
        organization1 = Organization.objects.get(name="Horde")
        organization2 = Organization.objects.get(name="Small Commonwealth")
        self.assertEqual(organization1.get_relationship_to(organization2).relationship, OrganizationRelationship.WAR)

    def test_get_war_relationship_from(self):
        organization1 = Organization.objects.get(name="Small Commonwealth")
        organization2 = Organization.objects.get(name="Horde")
        self.assertEqual(organization1.get_relationship_from(organization2).relationship, OrganizationRelationship.WAR)

    def test_convoke_elections(self):
        democracy = Organization.objects.get(name="Small Democracy")
        president = democracy.leader
        president.convoke_elections()
        self.assertEqual(PositionElection.objects.count(), 1)
        election = PositionElection.objects.get(id=1)
        self.assertEqual(election.position, president)
        self.assertEqual(election.turn, 6)
        self.assertEqual(election.closed, False)
        self.assertEqual(election.winner, None)
        self.assertEqual(election.open_candidacies().count(), 1)
        self.assertEqual(election.last_turn_to_present_candidacy(), 3)
        self.assertEqual(election.can_present_candidacy(), True)
        self.assertEqual(election.get_results().count(), 1)
        candidacy = PositionCandidacy.objects.get(id=1)
        self.assertEqual(candidacy.election, election)
        self.assertEqual(candidacy.candidate, president.get_position_occupier())
        self.assertEqual(candidacy.retired, False)

    def test_get_html_name(self):
        for organization in Organization.objects.all():
            html_name = organization.get_html_name()
            self.assertIn(organization.name, html_name)
            self.assertIn(organization.color, html_name)
            if organization.get_position_occupier():
                self.assertIn(organization.get_position_occupier().name, html_name)

    def test_get_default_stances(self):
        organization0 = Organization.objects.get(name="Small Democracy")
        organization1 = Organization.objects.get(name="Small Kingdom")
        organization2 = Organization.objects.get(name="Small Commonwealth")

        self.assertEqual(organization0.get_default_stance_to(organization1).get_stance(), MilitaryStance.DEFENSIVE)
        self.assertEqual(organization0.get_default_stance_to(organization2).get_stance(), MilitaryStance.DEFENSIVE)
        self.assertEqual(organization2.get_default_stance_to(organization0).get_stance(), MilitaryStance.DEFENSIVE)

    def test_get_diplomatically_based_default_stances(self):
        organization0 = Organization.objects.get(name="Small Democracy")
        organization1 = Organization.objects.get(name="Small Kingdom")
        relationship = organization0.get_relationship_to(organization1)
        relationship.set_relationship(OrganizationRelationship.WAR)
        self.assertEqual(organization0.get_default_stance_to(organization1).get_stance(), MilitaryStance.AGGRESSIVE)

        relationship.set_relationship(OrganizationRelationship.ALLIANCE)
        self.assertEqual(organization0.get_default_stance_to(organization1).get_stance(), MilitaryStance.AVOID_BATTLE)

    def test_get_diplomatically_based_default_stances2(self):
        organization0 = Organization.objects.get(name="Horde")
        organization1 = Organization.objects.get(name="Small Commonwealth")
        self.assertEqual(organization0.get_default_stance_to(organization1).get_stance(), MilitaryStance.AGGRESSIVE)
        self.assertEqual(organization1.get_default_stance_to(organization0).get_stance(), MilitaryStance.AGGRESSIVE)

    def test_specially_set_stances(self):
        organization0 = Organization.objects.get(name="Small Democracy")
        organization1 = Organization.objects.get(name="Small Kingdom")
        relationship = organization0.get_relationship_to(organization1)
        relationship.set_relationship(OrganizationRelationship.WAR)
        stance = organization0.get_default_stance_to(organization1)
        stance.stance_type = MilitaryStance.AVOID_BATTLE
        stance.save()
        self.assertEqual(organization0.get_default_stance_to(organization1).get_stance(), MilitaryStance.AVOID_BATTLE)

    def test_region_stance(self):
        organization0 = Organization.objects.get(name="Small Democracy")
        organization1 = Organization.objects.get(name="Small Kingdom")
        tile = Tile.objects.get(name="Some plains")
        stance = MilitaryStance.objects.create(
            from_organization=organization0,
            to_organization=organization1,
            region=tile,
            stance_type=MilitaryStance.AGGRESSIVE
        )
        result = organization0.get_region_stances_to(organization1)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result[0], stance)

        result = organization1.get_region_stances_to(organization0)
        self.assertEqual(result.count(), 0)

        result = organization0.get_region_stance_to(organization1, tile)
        self.assertEqual(result.get_stance(), MilitaryStance.AGGRESSIVE)

        result = organization0.get_region_stance_to(organization1, Tile.objects.get(name="Some forest"))
        self.assertEqual(result.get_stance(), MilitaryStance.DEFENSIVE)
