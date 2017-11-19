import math

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from character.models import Character
from decorators import inchar_required


@login_required
def activate(request, char_id):
    character = get_object_or_404(
        Character, pk=char_id, owner_user=request.user)
    request.session['character_id'] = character.id
    character.last_activation_time = timezone.now()
    character.save()
    return redirect('character:character_home')


@inchar_required
@require_POST
def public_order(request):
    if not request.hero.can_work_public_order():
        raise Http404("Can't do that")

    hours = int(request.POST.get('hours'))

    if hours < 1 or hours > request.hero.hours_in_turn_left:
        messages.error(request, 'You can\'t work that many ours.', 'danger')

    po_improvement = math.floor(
        hours / request.hero.location.population * 500
    )
    new_po = min(request.hero.location.public_order + po_improvement, 1000)

    message = 'You worked {} hours, improving the public order in ' \
              '{} from {}% to {}%' \
              ''.format(
                    hours,
                    request.hero.location,
                    request.hero.location.public_order / 10,
                    new_po / 10
              )

    request.hero.location.public_order = new_po
    request.hero.location.save()
    request.hero.hours_in_turn_left -= hours
    request.hero.save()

    messages.success(request, message, 'success')
    return redirect(reverse('character:character_home'))