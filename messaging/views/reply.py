from messaging.views.compose import ComposeView
from messaging.views.decorators import recipient_required_decorator


@recipient_required_decorator
def reply(request, recipient_id, prefilled_text=''):
    view = ComposeView()
    return view.get(
        request, reply_to=request.recipient, prefilled_text=prefilled_text)
