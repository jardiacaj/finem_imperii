from finem_imperii.build import GIT_REV


def git_revision_processor(request):
    return {'git_rev': GIT_REV}
