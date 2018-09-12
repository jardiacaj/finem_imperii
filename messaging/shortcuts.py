from django.template.loader import render_to_string

from messaging.models import CharacterMessage, MessageRecipient, \
    MessageRecipientGroup


def create_message(
        template, world, title, template_context=None, sender=None,
        link=None
):
    content = render_to_string(
        '{}'.format(template),
        template_context
    )
    return CharacterMessage.objects.create(
        content=content,
        creation_turn=world.current_turn,
        sender=sender,
        title=title,
        link=link
    )


def add_character_recipient(message: CharacterMessage, character, group=None):
    try:
        recipient = MessageRecipient.objects.get_or_create(
            message=message,
            character=character,
            defaults={'group': group}
        )[0]
        if recipient.group and not group:
            recipient.group = None
            recipient.save()
    except MessageRecipient.DoesNotExist:
        MessageRecipient.objects.create(
            message=message, character=character, group=group)


def add_organization_recipient(
        message: CharacterMessage,
        organization,
        add_lead_organizations=False
):
    group = MessageRecipientGroup.objects.get_or_create(
        message=message,
        organization=organization
    )[0]
    for character in organization.character_members.all():
        add_character_recipient(message, character, group)

    if add_lead_organizations:
        for lead_organization in organization.leaded_organizations.all():
            add_organization_recipient(message, lead_organization)


def add_recipients_for_reply(
        message: CharacterMessage, reply_to: MessageRecipient):
    for original_group in reply_to.message.messagerecipientgroup_set.all():
        add_organization_recipient(message, original_group.organization)
    for recipient in reply_to.message.messagerecipient_set.filter(
            group=None):
        add_character_recipient(message, recipient.character)
