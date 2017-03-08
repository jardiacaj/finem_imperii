from django.conf.urls import url

from account.views import login_view, logout_view, register_view, home
from messaging.views import clear_notifications, notification_list

urlpatterns = [
    url(r'^clear_notifications$', clear_notifications, name='clear_notifications'),
    url(r'^notifications$', notification_list, name='notification_list'),
]
