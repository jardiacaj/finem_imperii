from collections import namedtuple

from django import template

from world.turn import turn_to_date

register = template.Library()


@register.filter
def subtract(value, arg):
    return value - arg


@register.filter
def nice_turn(value):
    return turn_to_date(value)


Unit = namedtuple('Unit', ['multiplier', 'singular', 'plural'])
hour = Unit(multiplier=1, singular='hour', plural='hours')
day = Unit(multiplier=24, singular='day', plural='days')
month = Unit(multiplier=1, singular='month', plural='months')
year = Unit(multiplier=12, singular='year', plural='years')


def unit_breaker(value, units):
    unit = units[0]
    unit_amount = value // unit.multiplier
    rest = value % unit.multiplier
    suffix = ''
    following_units = units[1:]
    if not unit_amount and following_units:
        return unit_breaker(value, following_units)
    if rest and following_units:
        suffix = ' and {}'.format(unit_breaker(rest, following_units))
    return "{} {}{}".format(
        unit_amount,
        unit.singular if unit_amount == 1 else unit.plural,
        suffix
    )


@register.filter
def nice_hours(value):
    return unit_breaker(value, [day, hour])


@register.filter
def nice_turns(value):
    return unit_breaker(value, [year, month])
