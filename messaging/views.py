from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls.base import reverse
from django.views.generic.base import View

from decorators import inchar_required
from messaging.models import MessageRecipient, MessageRelationship, CharacterMessage, MessageRecipientGroup
from organization.models import Organization
from world.models import Character


def recipient_required_decorator(func):
    @inchar_required
    def inner(*args, **kwargs):
        recipient_id = kwargs.get('recipient_id')
        args[0].recipient = get_object_or_404(MessageRecipient, id=recipient_id, character=args[0].hero)
        return func(*args, **kwargs)
    return inner


@inchar_required
def home(request):
    context = {
        'tab': 'new',
        'recipient_list': request.hero.messagerecipient_set.filter(read=False)
    }
    return render(request, 'messaging/message_list.html', context)


class ComposeView(View):

    def get(self, request, character_id=None, prefilled_text='', reply_to=None):
        if character_id:
            target_character = get_object_or_404(Character, id=character_id, world=request.hero.world)
        else:
            target_character = None

        context = {
            'reply_to': reply_to,
            'prefilled_text': prefilled_text,
            'tab': 'compose',
            'target_character': target_character,
        }
        return render(request, 'messaging/compose.html', context)

    class RecipientBuildingException(Exception):
        pass

    @transaction.atomic
    def post(self, request):
        message_body = request.POST.get('message_body')
        reply_to = (
            get_object_or_404(MessageRecipient, id=request.POST.get('reply_to'), character=request.hero)
            if request.POST.get('reply_to') else None
        )

        if not message_body:
            messages.error(request, "Please write some message.", "danger")
            return redirect(request.META.get('HTTP_REFERER', reverse('messaging:compose')))

        if len(message_body) > 10000:
            return self.fail_post_gracefully(request, reply_to, message_body, error_message="This message is too long.")

        if not reply_to and not request.POST.getlist('recipient'):
            return self.fail_post_gracefully(
                request, reply_to, message_body, error_message="You must choose at least one recipient."
            )

        message = CharacterMessage.objects.create(
            content=message_body,
            creation_turn=request.hero.world.current_turn,
            sender=request.hero,
            safe=False
        )

        if reply_to:
            message.add_recipients_for_reply(reply_to)
        else:
            try:
                self.create_recipients_from_post_data(request, message)
            except ComposeView.RecipientBuildingException as e:
                return self.fail_post_gracefully(
                    request, reply_to, message_body, error_message=str(e)
                )

        messages.success(request, "Message sent.", "success")
        return redirect('messaging:sent')

    def fail_post_gracefully(self, request, reply_to, prefilled_body, error_message):
        messages.error(request, error_message, "danger")
        return self.get(request, None, prefilled_body, reply_to)

    def create_recipients_from_post_data(self, request, message):
        raw_recipients = request.POST.getlist('recipient')
        organization_count = 0
        character_count = 0

        for raw_recipient in raw_recipients:
            split = raw_recipient.split('_')

            if split[0] == 'settlement':
                for character in request.hero.location.character_set.all():
                    character_count += 1
                    message.add_recipient(character)
            elif split[0] == 'region':
                for character in Character.objects.filter(location__tile=request.hero.location.tile):
                    character_count += 1
                    message.add_recipient(character)
            elif split[0] == 'organization':
                organization_count += 1
                organization = get_object_or_404(Organization, id=split[1])
                group = MessageRecipientGroup.objects.create(message=message, organization=organization)
                for character in organization.character_members.all():
                    message.add_recipient(character, group)
            elif split[0] == 'character':
                character_count += 1
                character = get_object_or_404(Character, id=split[1])
                message.add_recipient(character)
            else:
                message.delete()
                raise ComposeView.RecipientBuildingException("Invalid recipient.")

        if organization_count > 4 or character_count > 40:
            message.delete()
            raise ComposeView.RecipientBuildingException("Too many recipients.")


@inchar_required
def add_contact(request, character_id):
    target_character = get_object_or_404(Character, id=character_id, world=request.hero.world)
    created = MessageRelationship.objects.get_or_create(from_character=request.hero, to_character=target_character)[1]
    if created:
        messages.success(request, "Character added to contacts", "success")
    return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))


@inchar_required
def remove_contact(request, character_id):
    target_character = get_object_or_404(Character, id=character_id, world=request.hero.world)
    try:
        target_relationship = MessageRelationship.objects.get(from_character=request.hero, to_character=target_character)
        target_relationship.delete()
        messages.success(request, "Character removed contacts", "success")
    except MessageRelationship.DoesNotExist:
        pass
    return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))


@inchar_required
def mark_all_read(request):
    MessageRecipient.objects.filter(character=request.hero, read=False).update(read=True)
    return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))


@recipient_required_decorator
def mark_read(request, recipient_id):
    request.recipient.read = not request.recipient.read
    request.recipient.save()
    return redirect(request.META.get('HTTP_REFERER', reverse('messaging:home')))


@recipient_required_decorator
def mark_favourite(request, recipient_id):
    request.recipient.favourite = not request.recipient.favourite
    request.recipient.save()
    return redirect(request.META.get('HTTP_REFERER', reverse('messaging:home')))


@inchar_required
def messages_list(request):
    context = {
        'tab': 'all',
        'recipient_list': request.hero.messagerecipient_set.all()
    }
    return render(request, 'messaging/message_list.html', context)


@inchar_required
def favourites_list(request):
    context = {
        'tab': 'favourites',
        'recipient_list': request.hero.messagerecipient_set.filter(favourite=True)
    }
    return render(request, 'messaging/message_list.html', context)


@inchar_required
def sent_list(request):
    context = {
        'tab': 'sent',
        'message_list': request.hero.messages_sent
    }
    return render(request, 'messaging/sent_list.html', context)


@recipient_required_decorator
def reply(request, recipient_id, prefilled_text=''):
    view = ComposeView()
    return view.get(request, reply_to=request.recipient, prefilled_text=prefilled_text)
