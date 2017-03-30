from django.test import TestCase

from organization.models import Organization, Capability, OrganizationRelationship, PositionElection, PositionCandidacy
from world.models import Character, Tile


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
        self.assertTrue(organization.is_part_of_violence_monopoly())

    def test_is_part_of_violence_monopoly2(self):
        organization = Organization.objects.get(name="Small King")
        self.assertTrue(organization.is_part_of_violence_monopoly())

    def test_is_part_of_violence_monopoly3(self):
        organization = Organization.objects.get(name="Governor of some plains")
        self.assertTrue(organization.is_part_of_violence_monopoly())

    def test_is_part_of_violence_monopoly4(self):
        organization = Organization.objects.get(name="Helper of the governor of some plains")
        self.assertTrue(organization.is_part_of_violence_monopoly())

    def test_is_part_of_violence_monopoly5(self):
        organization = Organization.objects.get(name="Small Federation")
        self.assertFalse(organization.is_part_of_violence_monopoly())

    def test_is_part_of_violence_monopoly6(self):
        organization = Organization.objects.get(name="President of the Small Federation")
        self.assertFalse(organization.is_part_of_violence_monopoly())

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
        self.assertEqual(len(external_capabilities), 8)
        self.assertTrue(external_capabilities.filter(type=Capability.BAN, organization__name="Small King").exists())

    def test_get_position_occupier(self):
        organization = Organization.objects.get(name="Small King")
        self.assertEqual(organization.get_position_occupier().id, 1)

    def test_get_position_occupier2(self):
        organization = Organization.objects.get(name="Small Kingdom")
        self.assertEqual(organization.get_position_occupier(), None)

    def test_get_relationship_to(self):
        organization1 = Organization.objects.get(name="Small Kingdom")
        organization2 = Organization.objects.get(name="Small commonwealth")
        self.assertEqual(organization1.get_relationship_to(organization2).relationship, OrganizationRelationship.PEACE)

    def test_get_relationship_from(self):
        organization1 = Organization.objects.get(name="Small Kingdom")
        organization2 = Organization.objects.get(name="Small King")
        self.assertEqual(organization1.get_relationship_from(organization2).relationship, OrganizationRelationship.PEACE)

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