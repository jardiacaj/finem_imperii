from django.conf.urls import url

from account.views import login_view, logout_view, register_view, home

urlpatterns = [
    url(r'^register/?$', register_view, name='register'),
    url(r'^login/?$', login_view, name='login'),
    url(r'^logout/?$', logout_view, name='logout'),
    url(r'^home/?$', home, name='home'),
]
