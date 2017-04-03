import random

files = {}


def load_file(filename):
    with open('name_generator/data_sources/{}'.format(filename)) as file:
        return [line.strip() for line in file]


def get_file(filename, limit):
    if filename not in files.keys():
        files[filename] = load_file(filename)
    name_list = files[filename]
    if limit is None:
        return name_list
    else:
        return random.sample(name_list, limit)


def get_names(limit=None):
    return get_file('names_both', limit)


def get_surnames(limit=None):
    return get_file('surnames', limit)


def get_female_names(limit=None):
    return get_file('names_female', limit)


def get_male_names(limit=None):
    return get_file('names_male', limit)


def generate_name(male):
    return (
            (get_female_names(1).pop() if not male else get_male_names(1).pop())
            + ' ' +
            get_surnames(1).pop()
        )
