from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View

from character.models import Character
from messaging.models import MessageRecipient
from messaging.shortcuts import create_message, add_recipients_for_reply, \
    add_character_recipient, add_organization_recipient
from organization.models import Organization


class ComposeException(Exception):
    pass


class ComposeView(View):
    def get(self,
            request, character_id=None, prefilled_text='', reply_to=None):
        if character_id:
            target_character = get_object_or_404(
                Character, id=character_id, world=request.hero.world)
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
            get_object_or_404(
                MessageRecipient,
                id=request.POST.get('reply_to'),
                character=request.hero
            )
            if request.POST.get('reply_to') else None
        )

        if not message_body:
            return self.fail_post_gracefully(
                request,
                reply_to,
                message_body,
                error_message="Please write some message."
            )

        if len(message_body) > 10000:
            return self.fail_post_gracefully(
                request,
                reply_to,
                message_body,
                error_message="This message is too long."
            )

        if not reply_to and not request.POST.getlist('recipient'):
            return self.fail_post_gracefully(
                request,
                reply_to,
                message_body,
                error_message="You must choose at least one recipient."
            )

        message = create_message(
            template='messaging/messages/character_written_message.html',
            world=request.hero.world,
            category=None,
            template_context={'content': message_body},
            sender=request.hero
        )

        if reply_to:
            add_recipients_for_reply(message, reply_to)
        else:
            try:
                self.create_recipients_from_post_data(request, message)
            except ComposeView.RecipientBuildingException as e:
                return self.fail_post_gracefully(
                    request, reply_to, message_body, error_message=str(e)
                )

        messages.success(request, "Message sent.", "success")
        return redirect('messaging:sent')

    def fail_post_gracefully(
            self, request, reply_to, prefilled_body, error_message):
        messages.error(request, error_message, "danger")
        return self.get(request, None, prefilled_body, reply_to)

    def create_recipients_from_post_data(self, request, message):
        raw_recipients = request.POST.getlist('recipient')
        organization_count = 0
        character_count = 0

        for raw_recipient in raw_recipients:
            split = raw_recipient.split('_')

            if split[0] == 'settlement':
                for character in request.hero.location.character_set.filter(
                        paused=False):
                    character_count += 1
                    add_character_recipient(message, character)
            elif split[0] == 'region':
                for character in Character.objects.filter(
                        location__tile=request.hero.location.tile,
                        paused=False):
                    character_count += 1
                    add_character_recipient(message, character)
            elif split[0] == 'organization':
                organization_count += 1
                organization = get_object_or_404(Organization, id=split[1])
                add_organization_recipient(message, organization)
            elif split[0] == 'character':
                character_count += 1
                character = get_object_or_404(Character, id=split[1])
                add_character_recipient(message, character)
            else:
                message.delete()
                raise ComposeView.RecipientBuildingException(
                    "Invalid recipient.")

        if organization_count > 4 or character_count > 40:
            message.delete()
            raise ComposeView.RecipientBuildingException(
                "Too many recipients.")
