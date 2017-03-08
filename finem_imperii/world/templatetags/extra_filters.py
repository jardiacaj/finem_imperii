from django import template

from world.turn import turn_to_date

register = template.Library()


@register.filter
def subtract(value, arg):
    return value - arg


@register.filter
def nice_turn(value):
    return turn_to_date(value)


@register.filter
def nice_hours(value):
    if value == 1:
        return "1 hour"
    elif value < 24:  # includes 0
        return "{} hours".format(value)
    elif value == 24:
        return "1 day"
    elif value < 48:
        return "1 day and {}".format(nice_hours(value % 24))
    else:
        return "{} days and {}".format(value // 24, nice_hours(value % 24))
