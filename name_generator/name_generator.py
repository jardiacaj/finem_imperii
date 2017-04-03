import random


def load_file(filename):
    with open('name_generator/data_sources/{}'.format(filename)) as file:
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
        return self.get_file('names_both', limit)

    def get_surnames(self, limit=None):
        return self.get_file('surnames', limit)

    def get_female_names(self, limit=None):
        return self.get_file('names_female', limit)

    def get_male_names(self, limit=None):
        return self.get_file('names_male', limit)

    def generate_name(self, male):
        return (
                (self.get_female_names(1).pop() if not male else self.get_male_names(1).pop())
                + ' ' +
                self.get_surnames(1).pop()
            )
