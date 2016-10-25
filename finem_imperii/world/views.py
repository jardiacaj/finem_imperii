from django.contrib.auth.decorators import login_required
from django.forms.models import ModelForm
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View

from world.models import Character


class CharacterCreationForm(ModelForm):
    class Meta:
        model = Character
        fields = ['name']


class CharacterCreationView(View):
    initial = {'name': 'Name'}
    form_class = CharacterCreationForm
    template_name = 'world/create_character.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            character = form.save(commit=False)
            character.owner_user = request.user
            character.save()

        return render(request, self.template_name, {'form': form})


@login_required
def activate_character(request, char_id):
    character = get_object_or_404(Character, pk=char_id, owner_user=request.user)
    request.session['character_id'] = character.id
    return redirect('battle:setup')
