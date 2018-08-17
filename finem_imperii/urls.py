from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include(('base.urls', 'base'), namespace='base')),
    url(r'^', include(('account.urls', 'account'), namespace='account')),
    url(r'^', include(('world.urls', 'world'), namespace='world')),
    url(r'^character/', include(('character.urls', 'character'), namespace='character')),
    url(r'^unit/', include(('unit.urls', 'unit'), namespace='unit')),
    url(r'^messaging/', include(('messaging.urls', 'messaging'), namespace='messaging')),
    url(r'^organization/', include(('organization.urls', 'organization'), namespace='organization')),
    url(r'^battle/', include(('battle.urls', 'battle'), namespace='battle')),
    url(r'^help/', include(('help.urls', 'help'), namespace='help')),
]
