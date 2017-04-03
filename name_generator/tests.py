from django.test import TestCase

from name_generator.name_generator import load_file, NameGenerator

testfile1_content = ['Foo', 'Bar', 'Hello', 'World']
testfile2_content = ['Bar']


class TestNameGenerator(TestCase):
    def test_load_testfile1(self):
        result = load_file('testfile1')
        self.assertEqual(len(result), 4)
        self.assertEqual(result, testfile1_content)

    def test_load_testfile2(self):
        result = load_file('testfile2')
        self.assertEqual(len(result), 1)
        self.assertEqual(result, testfile2_content)

    def test_get_testfile1_all(self):
        name_generator = NameGenerator()
        result = name_generator.get_file('testfile1', None)
        self.assertEqual(len(result), 4)
        self.assertEqual(result, testfile1_content)

    def test_get_testfile1_one(self):
        name_generator = NameGenerator()
        result = name_generator.get_file('testfile1', 1)
        self.assertEqual(len(result), 1)
        self.assertIn(result[0], testfile1_content)

    def test_cache(self):
        name_generator = NameGenerator()
        name_generator.get_file('testfile1', 1)
        self.assertEqual(name_generator.files['testfile1'], testfile1_content)

    def test_get_testfile2(self):
        name_generator = NameGenerator()
        result = name_generator.get_file('testfile2', None)
        self.assertEqual(len(result), 1)
        self.assertEqual(result, testfile2_content)
        result = name_generator.get_file('testfile2', 1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result, testfile2_content)

    def test_names_both(self):
        name_generator = NameGenerator()
        self.assertIn(name_generator.get_names(1)[0], load_file('names_both'))

    def test_names_female(self):
        name_generator = NameGenerator()
        self.assertIn(name_generator.get_female_names(1)[0], load_file('names_female'))

    def test_names_male(self):
        name_generator = NameGenerator()
        self.assertIn(name_generator.get_male_names(1)[0], load_file('names_male'))

    def test_surnames(self):
        name_generator = NameGenerator()
        self.assertIn(name_generator.get_surnames(1)[0], load_file('surnames'))

    def test_name_generation(self):
        name_generator = NameGenerator()
        name_generator.files = {
            'names_female': ['female'],
            'names_male': ['male'],
            'surnames': ['surname'],
        }
        self.assertEqual(name_generator.generate_name(False), "female surname")
        self.assertEqual(name_generator.generate_name(True), "male surname")
