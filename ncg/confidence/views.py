from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from .models import NflGame, NflTeam, Entry, Player, NflGameMgr
from .forms import EntryAddForm, EntryUpdateForm


def get_menu_list():

    menu_items = (('Login', 'login'),
                  ('NFL Schedule', 'confidence/current_games_list'),
                  ('Logout', 'login'),
                  ('Current Entry', 'confidence/current_entry'),

                  )
    print("WelcomePageView: get_menu_list: list->", menu_items)
    return menu_items


class PlayerEntryList(ListView):
    model = Entry
    template_name = 'confidence/playerentry_list.html'

    def get_context_data(self, **kwargs):
        context = super(PlayerEntryList, self).get_context_data(**kwargs)
        session_user = Player.get_player(context['view'].request.user.username)
        if 'player_id' in self.kwargs:
            player = Player.get_player(id=self.kwargs['player_id'])
        else:
            player = Player.get_player(context['view'].request.user.username)

        if 'week' in self.kwargs:
            week = self.kwargs['week']
        else:
            week = NflGame.get_nfl_week()
        season = NflGame.get_nfl_season()

        context['current_entry'] = Entry.get_player_entries(player=player, week=week)
        context['menu'] = get_menu_list()
        context['player'] = player
        context['session_user'] = session_user
        context['week'] = week
        context['season'] = season
        context['points_total'] = Entry.get_points_total(season=season, week=week, player=player)
        return context

    def get(self, request, *args, **kwargs):
        NflGameMgr.game_score_update()
        if request.user.is_authenticated:
            print('PlayerEntryList:authenticated_get->', request.user)
            return super(PlayerEntryList, self).get(request, *args, **kwargs)
        else:
            print('PlayerEntryList:not_authenticated_get->', request.user)
            return HttpResponseRedirect(reverse('login'))

class NflGameList(ListView):

    model = NflGame
    template_name = 'confidence/nflgame_list.html'

    def get_context_data(self, **kwargs):

        context = super(NflGameList, self).get_context_data(**kwargs)
        context['session_user'] = Player.get_player(context['view'].request.user.username)
        context['player'] = Player.get_player(context['view'].request.user.username)
        context['current_games'] = NflGame.current_games
        context['week'] = NflGame.get_nfl_week()
        context['season'] = NflGame.get_nfl_season()
        context['menu'] = get_menu_list()
        context['players'] = Player.get_current_players()
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            print('NflGameList:authenticated_get->', request.user)
            player = Player.get_player(username=request.user.username)
            print("NflGameList player->", player.first_name, player.last_name)
            player.check_entry()
            Entry.set_entry_locks()
            NflGameMgr.game_score_update()
            return super(NflGameList, self).get(request, *args, **kwargs)
        else:
            print('NflGameList:not_authenticated_get->', request.user)
            return HttpResponseRedirect(reverse('login'))

class TeamGameList(ListView):

    model = NflGame
    template_name = 'confidence/teamgame_list.html'

    def get_context_data(self, **kwargs):

        context = super(TeamGameList, self).get_context_data(**kwargs)
        context['session_user'] = Player.get_player(context['view'].request.user.username)
        team = NflTeam.objects.get(id=self.kwargs['team_id'])
        context['team'] = team
        context['team_games'] = team.get_completed_games()
        context['menu'] = get_menu_list()
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            print('TeamGameList:authenticated_get->', request.user)
            return super(TeamGameList, self).get(request, *args, **kwargs)
        else:
            print('TeamGameList:not_authenticated_get->', request.user)
            return HttpResponseRedirect(reverse('login'))


class UpdateEntry(CreateView):
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
        context['session_user'] = Player.get_player(context['view'].request.user.username)
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
            game_dict['conf'] = conf_fld_dict['confidence_'+ str(game.id)]
            game_list.append(game_dict.copy())
            #print('field->', game_dict['pick'], game_dict['conf'])
            game_dict.clear()
        context['menu'] = get_menu_list()
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
                    #data = form.cleaned_data.copy()
                    player = Player.get_player(request.user.username)
                    #data['player'].delete()
                    conf_dict = {}
                    pick_dict = {}
                    game_dict = {}
                    week = NflGame.get_nfl_week()
                    for key, value in form.cleaned_data.items():
                        fld_type, game_id = key.split('_')

                        if fld_type == 'pick':
                            pick_dict[game_id] = value
                            game = NflGame.get_game(id=game_id)
                            game_dict[game_id] = game
                        elif fld_type == 'confidence':
                            conf_dict[game_id] = int(value)
                    """ Clear the previous data  """
                    Entry.objects.filter(player=player, week=week).delete()

                    for game_id, game in game_dict.items():
                        if pick_dict[game_id] == '1':
                            projected_winner = game.home_team
                        elif pick_dict[game_id] == '2':
                            projected_winner = game.away_team
                        else:
                            projected_winner = None

                        e = Entry(player=player, season=game.season, week=game.week, nfl_game=game,
                                  is_winner=None, confidence=int(conf_dict[game_id]),
                                  pick_selection=int(pick_dict[game_id]), projected_winner=projected_winner)
                        e.save()
                        player.set_entry()
                        print('e->', e.player.first_name, e.id, game.season, game.week, projected_winner.name)

                    return HttpResponseRedirect(reverse('player_entry_list', kwargs={'player_id': player.id, 'week': week}))
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


class CreateEntry(CreateView):

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
        context['session_user'] = Player.get_player(context['view'].request.user.username)
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
            game_dict['conf'] = conf_fld_dict['confidence_'+ str(game.id)]
            game_list.append(game_dict.copy())
            #print('field->', game_dict['pick'], game_dict['conf'])
            game_dict.clear()
        context['menu'] = get_menu_list()
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
                    #data = form.cleaned_data.copy()
                    player = Player.get_player(request.user.username)
                    #data['player'].delete()
                    conf_dict = {}
                    pick_dict = {}
                    game_dict = {}
                    week = NflGame.get_nfl_week()
                    for key, value in form.cleaned_data.items():
                        fld_type, game_id = key.split('_')

                        if fld_type == 'pick':
                            pick_dict[game_id] = value
                            game = NflGame.get_game(id=game_id)
                            game_dict[game_id] = game
                        elif fld_type == 'confidence':
                            conf_dict[game_id] = value

                    for game_id, game in game_dict.items():
                        if pick_dict[game_id] == '1':
                            projected_winner = game.home_team
                        elif pick_dict[game_id] == '2':
                            projected_winner = game.away_team
                        else:
                            projected_winner = None

                        e = Entry(player=player, season=game.season, week=game.week, nfl_game=game,
                                  is_winner=None, confidence=int(conf_dict[game_id]),
                                  pick_selection=int(pick_dict[game_id]), projected_winner=projected_winner)
                        e.save()
                        player.set_entry()
                        print('e->', e.player.first_name, e.id, game.season, game.week, projected_winner.name)

                    return HttpResponseRedirect(reverse('player_entry_list', kwargs={'player_id': player.id, 'week': week}))
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