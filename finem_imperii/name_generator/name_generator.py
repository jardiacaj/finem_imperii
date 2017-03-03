import random


def load_file(filename):
    with open(filename) as file:
        return [line.strip() for line in file]


class NameGenerator:
    def __init__(self):
        self.files = {}

    def get_file(self, filename, limit):
        if filename not in self.files.keys():
            self.files[filename] = load_file(filename)
        name_list = self.files[filename]
        if limit is None:
            return name_list
        else:
            return random.sample(name_list, limit)

    def get_names(self, limit=None):
        return self.get_file('name_generator/data_sources/names_both', limit)

    def get_surnames(self, limit=None):
        return self.get_file('name_generator/data_sources/surnames', limit)

    def get_female_names(self, limit=None):
        return self.get_file('name_generator/data_sources/names_female', limit)

    def get_male_names(self, limit=None):
        return self.get_file('name_generator/data_sources/names_male', limit)
