from django.db.models.query_utils import Q

from world.models import NPC


def build_population_query(request, prefix):
    candidates = request.hero.location.npc_set.filter(able=True, unit=None)
    men_allowed = request.POST.get('{}men'.format(prefix))
    women_allowed = request.POST.get('{}women'.format(prefix))

    if men_allowed and women_allowed:
        pass
    elif men_allowed and not women_allowed:
        candidates = candidates.filter(male=True)
    elif not men_allowed and women_allowed:
        candidates = candidates.filter(male=False)
    elif not men_allowed and not women_allowed:
        raise Exception("You must choose at least one gender.")

    trained_allowed = request.POST.get('{}trained'.format(prefix))
    untrained_allowed = request.POST.get('{}untrained'.format(prefix))

    if trained_allowed and untrained_allowed:
        pass
    elif trained_allowed and not untrained_allowed:
        candidates = candidates.filter(trained_soldier=True)
    elif not trained_allowed and untrained_allowed:
        candidates = candidates.filter(trained_soldier=False)
    elif not trained_allowed and not untrained_allowed:
        raise Exception("You must choose at least one training group.")

    skill_queries = []
    if request.POST.get('{}skill_high'.format(prefix)):
        skill_queries.append(Q(skill_fighting__gte=NPC.TOP_SKILL_LIMIT))
    if request.POST.get('{}skill_medium'.format(prefix)):
        skill_queries.append(Q(skill_fighting__gte=NPC.MEDIUM_SKILL_LIMIT, skill_fighting__lt=NPC.TOP_SKILL_LIMIT))
    if request.POST.get('{}skill_low'.format(prefix)):
        skill_queries.append(Q(skill_fighting__lt=NPC.MEDIUM_SKILL_LIMIT))
    if len(skill_queries) == 0:
        raise Exception("You must choose at least one skill group")

    # See https://stackoverflow.com/questions/852414/how-to-dynamically-compose-an-or-query-filter-in-django
    query = skill_queries.pop()
    for item in skill_queries:
        query |= item
    candidates.filter(query)

    age_queries = []
    if request.POST.get('{}age_old'.format(prefix)):
        age_queries.append(Q(age_months__gte=NPC.OLD_AGE_LIMIT))
    if request.POST.get('{}age_middle'.format(prefix)):
        age_queries.append(Q(age_months__gte=NPC.MIDDLE_AGE_LIMIT, age_months__lt=NPC.OLD_AGE_LIMIT))
    if request.POST.get('{}age_young'.format(prefix)):
        age_queries.append(Q(age_months__gte=NPC.YOUNG_AGE_LIMIT, age_months__lt=NPC.MIDDLE_AGE_LIMIT))
    if request.POST.get('{}age_very_young'.format(prefix)):
        age_queries.append(Q(age_months__gte=NPC.VERY_YOUNG_AGE_LIMIT, age_months__lt=NPC.YOUNG_AGE_LIMIT))
    if len(skill_queries) == 0:
        raise Exception("You must choose at least one age group")

    # See https://stackoverflow.com/questions/852414/how-to-dynamically-compose-an-or-query-filter-in-django
    query = age_queries.pop()
    for item in age_queries:
        query |= item
    candidates.filter(query)

    return candidates
