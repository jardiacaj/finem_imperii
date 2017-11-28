from django.contrib import messages
from django.shortcuts import redirect


def redirect_back(request, default_url, error_message=None):
    if error_message is not None:
        messages.error(request, error_message, "danger")

    return redirect(
        request.META.get(
            'HTTP_REFERER',
            default_url
        )
    )
