from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic import CreateView, UpdateView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.http import HttpResponseRedirect, Http404, QueryDict
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.urls import reverse
from .models import NflGame, NflTeam, Entry, Player, NflGameMgr, PlayerEntry, TaskManager
from .forms import EntryAddForm, EntryUpdateForm
import random
import plotly.offline as opy
import plotly.graph_objs as go
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .tasks import task_nfl_score_update, task_nfl_score_update2, repeat_nfl_score_update


def get_menu_list(player=None):

    if player:
        player.set_last_access_time()

    menu_items = (
                  ('NFL Schedule', 'confidence/current_games_list'),
                  ('Current Entry', 'confidence/current_entry'),
                  ('Results', 'confidence/results_list'),
                  ('Head 2 Head', 'confidence/head2head_list'),
                  ('Logout', 'login'),
                  )
    #task_nfl_score_update.delay()
    print('get_menu_list- task id', TaskManager.get_task_id('repeat_nfl_score_update'))
    task = TaskManager.get_task('repeat_nfl_score_update')
    if task:
        print('get_menu_list- task status pre-run', task.status())
        print('get_menu_list- task id pre-run', task.get_task_id('repeat_nfl_score_update'))
        if task.is_complete():
            print('get_menu_list- task is_complete')
            result = repeat_nfl_score_update.delay()
            TaskManager.set_id(result.id, 'repeat_nfl_score_update')
            task = TaskManager.get_task('repeat_nfl_score_update')
            print('get_menu_list- task status', task.status())
            print('get_menu_list- task id', task.get_task_id('repeat_nfl_score_update'))
    else:
        result = repeat_nfl_score_update.delay()
        TaskManager.set_id(result.id, 'repeat_nfl_score_update')
    #NflGameMgr.game_score_update()
    print("WelcomePageView: get_menu_list: list->", menu_items)
    return menu_items


class ResultsList(LoginRequiredMixin,ListView):
    model = Entry
    template_name = 'confidence/results_list.html'

    def get_context_data(self, **kwargs):
        context = super(ResultsList, self).get_context_data(**kwargs)
        session_user = Player.get_player(context['view'].request.user.username)
        if 'player_id' in self.kwargs:
            player = Player.get_player(id=self.kwargs['player_id'])
        else:
            player = Player.get_player(context['view'].request.user.username)

        current_week = NflGame.get_nfl_week()
        season = NflGame.get_nfl_season()
        results = []

        week = {}

        for wk in range(13, current_week + 1):
            week['value'] = wk
            #NflGameMgr.game_score_update(week=wk)
            task_nfl_score_update2.delay()
            if wk == NflGame.get_nfl_week():
                week['tab_class'] = 'tab-pane fade in active'
            else:
                week['tab_class'] = 'tab-pane fade'
            week['players'] = PlayerEntry.objects.filter(season=NflGame.get_nfl_season(), week=wk).order_by('-points_earned')

            results.append(week.copy())
            week.clear()

        print('ResultsList: results->', results)

        context['results'] = results
        context['menu'] = get_menu_list(player=session_user)
        context['player'] = player
        context['session_user'] = session_user
        context['week'] = week
        context['season'] = season

        return context


class Head2HeadView(ListView):
    model = Entry
    template_name = 'confidence/head2head_list.html'

    def get_context_data(self, **kwargs):
        context = super(Head2HeadView, self).get_context_data(**kwargs)
        session_user = Player.get_player(context['view'].request.user.username)
        if 'player_id' in self.kwargs:
            player = Player.get_player(id=self.kwargs['player_id'])
        else:
            player = Player.get_player(context['view'].request.user.username)

        if 'week' in self.kwargs:
            week = self.kwargs['week']
            print('PlayerEntryList-week in kwargs->', week, self.kwargs)
        else:
            week = NflGame.get_nfl_week()
            print('PlayerEntryList-week NOT in kwargs->', week, self.kwargs)
        season = NflGame.get_nfl_season()

        players = []
        for entry in PlayerEntry.objects.filter(season=season, week=week).order_by('player'):
            players.append(entry.player)

        games = NflGame.objects.filter(season=season, week=week).order_by('game_time', 'id')
        context['menu'] = get_menu_list(player=session_user)
        context['player'] = player
        context['session_user'] = session_user
        context['week'] = week
        context['season'] = season
        context['games'] = games
        context['players'] = players

        return context



class PlayerEntryList(LoginRequiredMixin, ListView):
    model = Entry
    template_name = 'confidence/playerentry_list.html'

    def get_context_data(self, **kwargs):
        context = super(PlayerEntryList, self).get_context_data(**kwargs)
        session_user = Player.get_player(context['view'].request.user.username)
        print('PlayerEntryList->kwargs', self.kwargs)
        if 'player_id' in self.kwargs:
            player = Player.get_player(id=self.kwargs['player_id'])
        else:
            player = Player.get_player(context['view'].request.user.username)

        if 'week' in self.kwargs:
            week = self.kwargs['week']
            print('PlayerEntryList-week in kwargs->', week, self.kwargs)
        else:
            week = NflGame.get_nfl_week()
            print('PlayerEntryList-week NOT in kwargs->', week, self.kwargs)
        season = NflGame.get_nfl_season()
        if session_user == player:
            context['current_entry'] = Entry.get_player_entries(player=player, week=week)
        else:
            context['current_entry'] = Entry.get_player_entries(player=player, week=week, sort='date')

        player_entry = PlayerEntry.objects.get(season=season, week=week, player=player)
        print('PlayerEntryList: points earned->', player_entry.get_points_earned())

        context['menu'] = get_menu_list(player=session_user)
        context['player'] = player
        context['session_user'] = session_user
        context['week'] = week
        context['season'] = season
        context['points_total'] = player_entry.get_points_earned()
        return context

    def get(self, request, *args, **kwargs):
        #NflGameMgr.game_score_update()
        if request.user.is_authenticated:
            print('PlayerEntryList:authenticated_get->', request.user)
            return super(PlayerEntryList, self).get(request, *args, **kwargs)
        else:
            print('PlayerEntryList:not_authenticated_get->', request.user)
            return HttpResponseRedirect(reverse('login'))


class NflGameList(LoginRequiredMixin, ListView):

    model = NflGame
    template_name = 'confidence/nflgame_list.html'

    def get_context_data(self, **kwargs):
        context = super(NflGameList, self).get_context_data(**kwargs)
        session_user = Player.get_player(context['view'].request.user.username)
        context = super(NflGameList, self).get_context_data(**kwargs)
        context['session_user'] = session_user
        context['player'] = Player.get_player(context['view'].request.user.username)
        context['current_games'] = NflGame.current_games
        context['week'] = NflGame.get_nfl_week()
        context['season'] = NflGame.get_nfl_season()
        context['menu'] = get_menu_list(player=session_user)
        players = Player.get_current_players()
        context['players'] = players

        player_list = []
        player_pts = []
        player_lost_pts =[]
        player_rem_pts = []
        for player in players:
            print("player points->", player.current_points)
            player_list.append(player.first_name + " " + player.last_name)
            player_pts.append(player.current_points['points'])
            player_lost_pts.append(player.current_points['lost_points'])
            player_rem_pts.append(player.current_points['remain_points'])
        player_list.reverse()
        player_pts.reverse()
        player_lost_pts.reverse()
        player_rem_pts.reverse()
        trace1 = go.Bar(
            y=player_list,
            x=player_pts,
            name='Points',
            orientation = 'h',
            marker = dict(
                color = 'rgba(51, 204, 51, 0.6)',
                line = dict(
                    color = 'rgba(51, 204, 51, 1.0)',
                    width = 1)
            )
        )
        trace2 = go.Bar(
            y=player_list,
            x=player_rem_pts,
            name='Remaining Points',
            orientation = 'h',
            marker = dict(
                color = 'rgba(0, 153, 255, 0.6)',
                line = dict(
                    color = 'rgba(0, 153, 255, 1.0)',
                    width = 1)
            )
        )
        trace3 = go.Bar(
            y=player_list,
            x=player_lost_pts,
            name='Lost Points',
            orientation = 'h',
            marker = dict(
                color = 'rgba(204, 51, 0, 0.6)',
                line = dict(
                    color = 'rgba(204, 51, 0, 1.0)',
                    width = 1)
            )
        )

        data = [trace1, trace2, trace3]
        layout = go.Layout(
            barmode='stack',
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        fig = go.Figure(data=data, layout=layout)
        div = opy.plot(fig, filename='marker-h-bar', output_type='div')


        context['graph'] = div


        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            print('NflGameList:authenticated_get->', request.user)
            player = Player.get_player(username=request.user.username)
            print("NflGameList player->", player.first_name, player.last_name)
            player.check_entry()
            Entry.set_entry_locks()
            #NflGameMgr.game_score_update()
            #PlayerEntry.build_entry()
            return super(NflGameList, self).get(request, *args, **kwargs)
        else:
            print('NflGameList:not_authenticated_get->', request.user)
            return HttpResponseRedirect(reverse('login'))


class TeamGameList(LoginRequiredMixin, ListView):

    model = NflGame
    template_name = 'confidence/teamgame_list.html'

    def get_context_data(self, **kwargs):

        context = super(TeamGameList, self).get_context_data(**kwargs)
        session_user = Player.get_player(context['view'].request.user.username)
        context['session_user'] = session_user
        team = NflTeam.objects.get(id=self.kwargs['team_id'])
        context['team'] = team
        context['team_games'] = team.get_completed_games()
        context['menu'] = get_menu_list(player=session_user)
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            print('TeamGameList:authenticated_get->', request.user)
            return super(TeamGameList, self).get(request, *args, **kwargs)
        else:
            print('TeamGameList:not_authenticated_get->', request.user)
            return HttpResponseRedirect(reverse('login'))


class UpdateEntry(LoginRequiredMixin, CreateView):
    model = Entry
    form_class = EntryUpdateForm
    template_name = 'confidence/update_entry.html'
    success_url = 'confidence/current_games_list'

    def get_form_kwargs(self):
        kwargs = super(UpdateEntry, self).get_form_kwargs()
        kwargs['player_id'] = self.kwargs.get('player_id')
        kwargs['week'] = self.kwargs.get('week')
        print('UpdateEntry: get_form_kwargs->', kwargs)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(UpdateEntry, self).get_context_data(**kwargs)
        pick_fld_dict = {}
        conf_fld_dict = {}
        player = Player.get_player(context['view'].request.user.username)
        context['player'] = player
        session_user = Player.get_player(context['view'].request.user.username)
        context['session_user'] = session_user
        for fld in context['form'].visible_fields():
            if fld.name[:4] == 'pick':
                pick_fld_dict[fld.name] = fld
            else:
                conf_fld_dict[fld.name] = fld

        game_list = []
        game_dict = {}
        for game in NflGame.current_games.all():
            game_dict['game'] = game
            game_dict['pick'] = pick_fld_dict['pick_'+ str(game.id)]
            #game_dict['conf'] = conf_fld_dict['confidence_'+ str(game.id)]
            game_list.append(game_dict.copy())
            #print('field->', game_dict['pick'], game_dict['conf'])
            game_dict.clear()
        context['menu'] = get_menu_list(player=session_user)
        context['current_games'] = game_list

        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            print('UpdateEntry:authenticated_get->', request.user)
            return super(UpdateEntry, self).get(request, *args, **kwargs)
        else:
            print('UpdateEntry:not_authenticated_get->', request.user)
            return HttpResponseRedirect(reverse('login'))

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)
        if request.user.is_authenticated:
            print('UpdateEntry:authenticated_post->', request.user)
            if form.is_bound:
                print("form bound")

                if form.is_valid():
                    print("form valid")
                    print("form-cleaned_data->", form.cleaned_data)

                    player_entry = Entry.create_update_entries(entries=form.cleaned_data,
                                                               username=request.user.username,
                                                               mode='update')
                    if 'fail' in player_entry:
                        self.raise_exception = True
                        messages.error(request, player_entry['fail'])
                        return HttpResponseRedirect(reverse('current_games_list'))
                    else:
                        return HttpResponseRedirect(reverse('sort_entry', kwargs={'pk': player_entry['success'].id}))
                else:
                    print("form not valid", form.errors)
                    return super(UpdateEntry, self).post(request, *args, **kwargs)

            else:
                print("form NOT bound")
                return super(UpdateEntry, self).post(request, *args, **kwargs)
        else:
            # Do something for anonymous users.
            print('UpdateEntry:not_authenticated_post->', request.user)
            return HttpResponseRedirect(reverse('login'))


class CreateEntry(LoginRequiredMixin, CreateView):

    model = Entry
    form_class = EntryAddForm
    template_name = 'confidence/create_entry.html'
    success_url = 'confidence/current_games_list'

    def get_context_data(self, **kwargs):
        context = super(CreateEntry, self).get_context_data(**kwargs)
        pick_fld_dict = {}
        conf_fld_dict = {}
        player = Player.get_player(context['view'].request.user.username)
        context['player'] = player
        session_user = Player.get_player(context['view'].request.user.username)
        context['session_user'] = session_user
        for fld in context['form'].visible_fields():
            if fld.name[:4] == 'pick':
                pick_fld_dict[fld.name] = fld
            else:
                conf_fld_dict[fld.name] = fld

        game_list = []
        game_dict = {}
        for game in NflGame.current_games.all():
            game_dict['game'] = game
            game_dict['pick'] = pick_fld_dict['pick_'+ str(game.id)]
            #game_dict['conf'] = conf_fld_dict['confidence_'+ str(game.id)]
            game_list.append(game_dict.copy())
            #print('field->', game_dict['pick'], game_dict['conf'])
            game_dict.clear()
        context['menu'] = get_menu_list(player=session_user)
        context['current_games'] = game_list

        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            print('CreateEntry:authenticated_get->', request.user)
            return super(CreateEntry, self).get(request, *args, **kwargs)
        else:
            print('CreateEntry:not_authenticated_get->', request.user)
            return HttpResponseRedirect(reverse('login'))

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)
        if request.user.is_authenticated:
            print('CreateEntry:authenticated_post->', request.user)
            if form.is_bound:
                print("form bound")

                if form.is_valid():
                    print("form valid")
                    print("form-cleaned_data->", form.cleaned_data)

                    player_entry = Entry.create_update_entries(entries=form.cleaned_data,
                                                               username=request.user.username,
                                                               mode='create')

                    if 'fail' in player_entry:
                        self.raise_exception = True
                        messages.error(request, player_entry['fail'])
                        return HttpResponseRedirect(reverse('current_games_list'))
                    else:
                        return HttpResponseRedirect(reverse('sort_entry', kwargs={'pk': player_entry['success'].id}))
                else:
                    print("form not valid", form.errors)
                    return super(CreateEntry, self).post(request, *args, **kwargs)

            else:
                print("form NOT bound")
                return super(CreateEntry, self).post(request, *args, **kwargs)
        else:
            # Do something for anonymous users.
            print('CreateEntry:not_authenticated_post->', request.user)
            return HttpResponseRedirect(reverse('login'))


class SortEntry(LoginRequiredMixin, UpdateView):
    model = PlayerEntry
    fields = ['player', 'season', 'week', 'is_active']
    template_name = 'confidence/sort_entry.html'

    def get_context_data(self, **kwargs):
        context = super(SortEntry, self).get_context_data(**kwargs)
        player_entries = self.object.get_entries()
        self.object.active_confidence_values.clear()
        for entry in player_entries:
            if not entry.is_locked:
                self.object.active_confidence_values.append(entry.confidence)

        print('SortEntry: active_confidence_values->', self.object.active_confidence_values)
        game_conf_index = []
        for cntr in range(NflGame.get_game_count(NflGame.get_nfl_week()),0,-1):
            game_conf_index.append(cntr)
        context['index'] = game_conf_index
        context['entry_list'] = player_entries
        context['menu'] = get_menu_list()

        return context


def resort_entry(request):
    entries = QueryDict(request.POST['content'])
    for index, entry_id in enumerate(entries.getlist('entry[]')):
        entry = Entry.get_entry(id=entry_id)
        player_entry = PlayerEntry.get_entry(player=entry.player, week=entry.week, season=entry.season)

        orig_conf = entry.confidence
        entry.confidence = player_entry.active_confidence_values[index]
        entry.save()

        print('index->', index, 'entry_id->', entry_id, entry.projected_winner, player_entry.active_confidence_values[index], "orig->", orig_conf)
        # save index of entry_id as it's new order value
    return HttpResponseRedirect(reverse('sort_entry', kwargs={'pk': player_entry.id}))