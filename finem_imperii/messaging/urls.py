from django.conf.urls import url

from messaging.views import mark_all_read, messages_list, home

urlpatterns = [
    url(r'^messaging$', home, name='home'),
    url(r'^clear_notifications$', mark_all_read, name='mark_all_read'),
    url(r'^messaging/all$', messages_list, name='messages_list'),
]
