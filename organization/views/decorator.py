from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse

from decorators import inchar_required
from organization.models import Capability


def capability_required_decorator(func):
    @inchar_required
    def inner(*args, **kwargs):
        def fail_the_request(*args, **kwargs):
            messages.error(args[0], "You cannot do that", "danger")
            return redirect(args[0].META.get('HTTP_REFERER', reverse('world:character_home')))
        capability_id = kwargs.get('capability_id')
        if capability_id is None:
            capability_id = args[0].POST.get('capability_id')
        if capability_id is None:
            capability_id = args[0].GET.get('capability_id')
        capability = get_object_or_404(Capability, id=capability_id)
        if not capability.organization.character_can_use_capabilities(args[0].hero):
            return fail_the_request(*args, **kwargs)
        return func(*args, **kwargs)
    return inner