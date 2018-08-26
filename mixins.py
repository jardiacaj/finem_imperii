from django.contrib.contenttypes.models import ContentType
from django.urls import reverse


class AdminURLMixin(object):
    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (
            content_type.app_label,
            content_type.model),
            args=(self.id,))