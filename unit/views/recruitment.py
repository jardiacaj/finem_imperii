from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, redirect
from django.views import View

from unit.models import WorldUnit, unit_cost
from unit.recruitment import build_population_query_from_request, \
    BadPopulation, sample_candidates, recruit_unit


class RecruitmentView(View):
    template_name = 'unit/recruit.html'

    def get(self, request, *args, **kwargs):
        context = {
            'unit_types': WorldUnit.get_unit_types(nice=True),
            'can_recruit': request.hero.can_conscript()
        }
        return render(request, self.template_name, context)

    @staticmethod
    def fail_post_with_error(request, message):
        messages.add_message(
            request, messages.ERROR, message, extra_tags='danger'
        )
        return redirect('unit:recruit')

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        recruitment_type = request.POST.get('recruitment_type')
        if recruitment_type in ('conscription', 'professional'):
            if recruitment_type == 'conscription':
                prefix = 'conscript_'
            elif recruitment_type == 'professional':
                prefix = 'professional_'
            else:
                raise Http404()

            if not request.hero.can_conscript():
                return RecruitmentView.fail_post_with_error(
                    request,
                    "You can't conscript units here."
                )

            # get soldier count
            target_soldier_count = \
                int(request.POST.get('{}count'.format(prefix)))
            if not target_soldier_count > 0:
                return RecruitmentView.fail_post_with_error(
                    request, "Invalid number of soldiers."
                )

            # check cash
            if request.hero.cash < unit_cost(target_soldier_count):
                return RecruitmentView.fail_post_with_error(
                    request,
                    "You need {} silver coins to recruit a unit of {} "
                    "and you don't have that much.".format(
                        target_soldier_count,
                        target_soldier_count
                    )
                )

            # calculate time
            conscription_time = request.hero.location.conscription_time(
                target_soldier_count
            )

            if request.hero.hours_in_turn_left < conscription_time:
                return RecruitmentView.fail_post_with_error(
                    request,
                    "You need {} hours to recruit a unit of {}, but you don't "
                    "have that much time left in this turn.".format(
                        conscription_time,
                        target_soldier_count
                    )
                )

            # check unit type
            unit_type = request.POST.get('{}unit_type'.format(prefix))
            if unit_type not in WorldUnit.get_unit_types(nice=True):
                return RecruitmentView.fail_post_with_error(
                    request, "Invalid unit type."
                )

            # check payment
            """
            pay = int(request.POST.get('{}pay'.format(prefix)))
            if pay not in range(1, 7):
                return RecruitmentView.fail_post_with_error(
                    request, "Invalid payment."
                )

            if (
                    request.hero.worldunit_set.count() + 1 >
                    request.hero.max_units()
            ):
                return RecruitmentView.fail_post_with_error(
                    request, "You can't recruit any more units."
                )
            """

            already_recruited_soldier_count = sum(
                unit.soldier.count()
                for unit in request.hero.worldunit_set.all()
            )
            if (
                    already_recruited_soldier_count + target_soldier_count >
                    request.hero.max_soldiers()
            ):
                return RecruitmentView.fail_post_with_error(
                    request, "You can't recruit that many soldiers."
                )


            # get candidates

            try:
                candidates = build_population_query_from_request(
                    request, prefix, request.hero.location
                )
            except BadPopulation as e:
                return RecruitmentView.fail_post_with_error(request, e)

            if candidates.count() == 0:
                return RecruitmentView.fail_post_with_error(
                    request,
                    "You seem unable to find anyone in {} matching the profile"
                    " you want".format(request.hero.location)
                )

            soldiers = sample_candidates(candidates, target_soldier_count)

            unit = recruit_unit(
                "{}'s new unit".format(request.hero),
                request.hero,
                request.hero.location,
                soldiers,
                recruitment_type,
                unit_type
            )
            unit.mobilize()

            request.hero.hours_in_turn_left -= conscription_time
            request.hero.cash -= unit.monthly_cost()
            request.hero.save()

            messages.success(
                request,
                "You formed a new unit of {} called {}".format(
                    len(soldiers), unit.name
                ),
                "success"
            )
            return redirect(unit.get_absolute_url())

        else:
            pass