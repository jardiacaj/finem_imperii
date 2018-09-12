def send_notification_to_characters(character_set, template, title,
                                    template_context):
    for character in character_set.all():
        character.add_notification(template, title, template_context)
