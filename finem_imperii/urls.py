from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('base.urls', namespace='base'), name='base'),
    url(r'^', include('account.urls', namespace='account'), name='account'),
    url(r'^', include('world.urls', namespace='world'), name='world'),
    url(r'^character/', include('character.urls', namespace='character'), name='character'),
    url(r'^unit/', include('unit.urls', namespace='unit'), name='unit'),
    url(r'^messaging/', include('messaging.urls', namespace='messaging'), name='messaging'),
    url(r'^organization/', include('organization.urls', namespace='organization'), name='organization'),
    url(r'^battle/', include('battle.urls', namespace='battle'), name='battle'),
    url(r'^help/', include('help.urls', namespace='help'), name='help'),
]
