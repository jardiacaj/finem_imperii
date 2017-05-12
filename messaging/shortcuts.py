from messaging.models import CharacterMessage, MessageRecipient, \
    MessageRecipientGroup


def create_message(sender, category, world, safe, content):
    return CharacterMessage.objects.create(
        content=content,
        creation_turn=world.current_turn,
        sender=sender,
        safe=safe,
        category=category
    )


def add_character_recipient(message, character, group=None):
    try:
        recipient = MessageRecipient.objects.get(
            message=message, character=character)
        if recipient.group and not group:
            recipient.group = None
            recipient.save()
    except MessageRecipient.DoesNotExist:
        MessageRecipient.objects.create(
            message=message, character=character, group=group)


def add_organization_recipient(message, organization):
    group = MessageRecipientGroup.objects.create(
        message=message,
        organization=organization
    )
    for character in organization.character_members.all():
        add_character_recipient(message, character, group)


def add_recipients_for_reply(message, reply_to):
    for original_group in reply_to.message.messagerecipientgroup_set.all():
        new_group = MessageRecipientGroup.objects.create(
            message=message,
            organization=original_group.organization
        )
        for character in original_group.organization.character_members.all():
            MessageRecipient.objects.create(message=message,
                                            character=character,
                                            group=new_group)
    for recipient in reply_to.message.messagerecipient_set.filter(
            group=None):
        MessageRecipient.objects.create(message=message,
                                        character=recipient.character)
