import random
from collections import namedtuple

WeightedChoice = namedtuple("WeightedChoice", ['value', 'weight'])


def weighted_choice(choices):
    total_weights = sum(choice.weight for choice in choices)
    r = random.randrange(0, total_weights)
    v = 0
    for choice in choices:
        v += choice.weight
        if r < v:
            return choice.value
    raise Exception("Should never reach this point")
