from django.conf.urls import url

from messaging.views import clear_notifications, notification_list, home

urlpatterns = [
    url(r'^messaging$', home, name='home'),
    url(r'^clear_notifications$', clear_notifications, name='clear_notifications'),
    url(r'^notifications$', notification_list, name='notification_list'),
]
