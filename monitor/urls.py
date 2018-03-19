from django.conf.urls import url
from . import views

app_name = 'monitor'

urlpatterns = [
    url(r'^download/stats/$', views.get_json_information, name='download_stats'),
    url(r'^$', views.main_base_view, name='main_base'),
    url(r'^remove&update/$', views.remove_update, name='remove_update'),
    url(r'^ssh_info/(?P<pk>[0-9]+)/$', views.ssh_information_view, name='ssh_information'),
    url(r'^ajax/ssh_command/$', views.ssh_client_command, name='ssh_command'),
    url(r'^ajax/get_info_client/$', views.get_info_client, name='get_info'),
    url(r'^ajax/test_connection_client/$', views.test_connection_client, name='test_connection'),
]
