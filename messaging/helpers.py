def send_notification_to_characters(character_set, category, content, safe=False):
    for character in character_set.all():
        character.add_notification(category, content, safe)
