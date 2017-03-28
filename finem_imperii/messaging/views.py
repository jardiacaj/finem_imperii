from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls.base import reverse
from django.views.generic.base import View

from decorators import inchar_required
from messaging.models import MessageReceiver, MessageRelationship, CharacterMessage, MessageReceiverGroup
from organization.models import Organization
from world.models import Character


@inchar_required
def home(request):
    context = {
        'tab': 'new',
        'receiver_list': request.hero.messagereceiver_set.filter(read=False)
    }
    return render(request, 'messaging/message_list.html', context)


class ComposeView(View):
    def get(self, request, character_id=None, prefilled_text=''):
        if character_id:
            target_character = get_object_or_404(Character, id=character_id, world=request.hero.world)
        else:
            target_character = None

        context = {
            'prefilled_text': prefilled_text,
            'tab': 'compose',
            'target_character': target_character,
        }
        return render(request, 'messaging/compose.html', context)

    @transaction.atomic
    def post(self, request):
        message_body = request.POST.get('message_body')
        raw_receivers = request.POST.getlist('receiver')

        if not message_body:
            messages.error(request, "Please write some message.", "danger")
            return redirect(request.META.get('HTTP_REFERER', reverse('messaging:compose')))

        if len(message_body) > 10000:
            messages.error(request, "This message is too long.", "danger")
            return self.get(request, prefilled_text=message_body)

        if not raw_receivers:
            messages.error(request, "You must choose at least one receiver.", "danger")
            return self.get(request, prefilled_text=message_body)

        message = CharacterMessage.objects.create(
            content=message_body,
            creation_turn=request.hero.world.current_turn,
            sender=request.hero,
            safe=False
        )

        organization_count = 0
        character_count = 0

        for raw_receiver in raw_receivers:
            split = raw_receiver.split('_')

            if split[0] == 'settlement':
                for character in request.hero.location.character_set.all():
                    character_count += 1
                    MessageReceiver.objects.create(message=message, character=character)
            elif split[0] == 'region':
                for character in Character.objects.filter(location__tile=request.hero.location.tile):
                    character_count += 1
                    MessageReceiver.objects.create(message=message, character=character)
            elif split[0] == 'organization':
                organization_count += 1
                organization = get_object_or_404(Organization, id=split[1])
                group = MessageReceiverGroup.objects.create(message=message, organization=organization)
                for character in organization.character_members.all():
                    MessageReceiver.objects.create(message=message, character=character, group=group)
            elif split[0] == 'character':
                character_count += 1
                character = get_object_or_404(Character, id=split[1])
                MessageReceiver.objects.create(message=message, character=character)
            else:
                messages.error(request, "Invalid receiver.", "danger")
                return self.get(request, prefilled_text=message_body)

        if organization_count > 4 or character_count > 40:
            message.delete()
            messages.error(request, "Too many receivers.", "danger")
            return self.get(request, prefilled_text=message_body)

        messages.success(request, "Message sent.", "success")
        return redirect('messaging:sent')


@inchar_required
def favourite(request, character_id):
    target_character = get_object_or_404(Character, id=character_id, world=request.hero.world)
    MessageRelationship.objects.get_or_create(from_character=request.hero, to_character=target_character)
    return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))


@inchar_required
def unfavourite(request, character_id):
    target_character = get_object_or_404(Character, id=character_id, world=request.hero.world)
    target_relationship = get_object_or_404(MessageRelationship, from_character=request.hero, to_character=target_character)
    target_relationship.delete()
    return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))


@inchar_required
def mark_all_read(request):
    request.hero.unread_messages().all().update(read=True)
    return redirect(request.META.get('HTTP_REFERER', reverse('world:character_home')))


@inchar_required
def mark_read(request, receiver_id):
    receiver = get_object_or_404(MessageReceiver, id=receiver_id, character=request.hero)
    receiver.read = not receiver.read
    receiver.save()
    return redirect(request.META.get('HTTP_REFERER', reverse('messaging:home')))


@inchar_required
def mark_favourite(request, receiver_id):
    receiver = get_object_or_404(MessageReceiver, id=receiver_id, character=request.hero)
    receiver.favourite = not receiver.favourite
    receiver.save()
    return redirect(request.META.get('HTTP_REFERER', reverse('messaging:home')))


@inchar_required
def messages_list(request):
    context = {
        'tab': 'all',
        'receiver_list': request.hero.messagereceiver_set.all()
    }
    return render(request, 'messaging/message_list.html', context)


@inchar_required
def favourites_list(request):
    context = {
        'tab': 'favourites',
        'receiver_list': request.hero.messagereceiver_set.filter(favourite=True)
    }
    return render(request, 'messaging/message_list.html', context)


@inchar_required
def sent_list(request):
    context = {
        'tab': 'sent',
        'message_list': request.hero.messages_sent
    }
    return render(request, 'messaging/sent_list.html', context)
