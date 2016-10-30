from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.forms.models import ModelForm
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View

from battle.models import Battle, BattleCharacter
from decorators import inchar_required
from world.models import Character, WorldUnit


class CharacterCreationForm(ModelForm):
    class Meta:
        model = Character
        fields = ['name']


class CharacterCreationView(View):
    form_class = CharacterCreationForm
    template_name = 'world/create_character.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            character = form.save(commit=False)
            character.owner_user = request.user
            character.cash = 1000
            character.save()
            return redirect(reverse('world:activate_character', kwargs={'char_id': character.id}))
        else:
            return render(request, self.template_name, {'form': form})


class RectruitForm(ModelForm):
    class Meta:
        model = WorldUnit
        fields = ['name', 'power']


class RecruitView(View):
    form_class = RectruitForm
    template_name = 'world/recruit.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            unit = form.save(commit=False)

            if request.hero.cash < unit.power * 5:
                messages.error(request, "Not enough gold coins!")
                return self.get(request)

            unit.owner_character = request.hero
            request.hero.cash -= unit.power * 5
            request.hero.save()
            unit.save()
            return redirect(reverse('world:character_home'))
        else:
            return render(request, self.template_name, {'form': form})


@login_required
def activate_character(request, char_id):
    character = get_object_or_404(Character, pk=char_id, owner_user=request.user)
    request.session['character_id'] = character.id
    return redirect('world:character_home')


@inchar_required
def character_home(request):
    return render(request, 'world/character_home.html')


@inchar_required
def setup_battle(request, rival_char_id=None):
    if rival_char_id is None:
        rivals = Character.objects.exclude(pk=request.hero.pk)
        return render(request, 'world/setup_battle.html', context={'rivals': rivals})
    else:
        if rival_char_id == request.hero.id:
            messages.error("Cannot battle yourself!")
            return setup_battle(request)
        rival = get_object_or_404(Character, id=rival_char_id)
        battle = Battle()
        battle.save()
        battle.start_battle(request.hero, rival)
        return redirect(reverse('battle:setup', kwargs={'battle_id': battle.id}))
