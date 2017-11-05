def send_notification_to_characters(character_set, template, category,
                                    template_context):
    for character in character_set.all():
        character.add_notification(template, category, template_context)
