from django.shortcuts import render

from decorators import inchar_required


@inchar_required
def generic_message_list(request, tab, recipient_list,
                         template='messaging/message_list.html'):
    context = {
        'tab': tab,
        'recipient_list': recipient_list
    }
    return render(request, template, context)


@inchar_required
def home(request):
    return generic_message_list(
        request,
        tab='new',
        recipient_list=request.hero.messagerecipient_set.filter(read=False)
    )


@inchar_required
def messages_list(request):
    return generic_message_list(
        request,
        tab='all',
        recipient_list=request.hero.messagerecipient_set.all()
    )


@inchar_required
def favourites_list(request):
    return generic_message_list(
        request,
        tab='favourites',
        recipient_list=request.hero.messagerecipient_set.filter(
            favourite=True
        )
    )


@inchar_required
def sent_list(request):
    context = {
        'tab': 'sent',
        'message_list': request.hero.messages_sent
    }
    return render(request, 'messaging/sent_list.html', context)
