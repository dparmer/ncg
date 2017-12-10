from django.conf.urls import url
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    url(r'^login/$', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(next_page=reverse_lazy('login')), name='logout'),
    url(r'^current_games_list/$', views.NflGameList.as_view(), name='current_games_list'),
    url(r'^results_list/$', views.ResultsList.as_view(), name='results_list'),
    url(r'^team/(?P<team_id>[0-9]+)/$', views.TeamGameList.as_view(), name='team_games_list'),
    url(r'^entry/(?P<player_id>[0-9]+)/(?P<week>[0-9]+)/$', views.PlayerEntryList.as_view(), name='player_entry_list'),
    url(r'^current_entry/$', views.PlayerEntryList.as_view(), name='current_entry_list'),
    url(r'^create_entry/$', views.CreateEntry.as_view(), name='create_entry'),
    url(r'^update_entry/(?P<player_id>[0-9]+)/(?P<week>[0-9]+)/$', views.UpdateEntry.as_view(), name='update_entry'),
    url(r'^sort_entry/(?P<pk>[0-9]+)/$', views.SortEntry.as_view(), name='sort_entry'),
    url(r'^jquery/resort_entry/$', views.resort_entry, name='resort_entry'),

]

