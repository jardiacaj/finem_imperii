from django.conf.urls import url

from world.views import world_view, \
    minimap_view, world_view_iframe, tile_view, \
    tile_view_iframe

urlpatterns = [
    url(r'^tile/(?P<tile_id>[0-9]+)$', tile_view, name='tile'),
    url(r'^tile_iframe/(?P<tile_id>[0-9]+)$', tile_view_iframe, name='tile_iframe'),
    url(r'^world/(?P<world_id>[0-9]+)$', world_view, name='world'),
    url(r'^world_iframe/(?P<world_id>[0-9]+)$', world_view_iframe, name='world_iframe'),
    url(r'^minimap$', minimap_view, name='minimap'),
]
