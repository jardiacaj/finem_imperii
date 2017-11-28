from django.contrib.auth.models import User

from character.models import Character


def can_create_character(user: User) -> bool:
    if user.is_superuser:
        return True
    if Character.objects.filter(owner_user=user).count() < 4:
        return True
    return False
