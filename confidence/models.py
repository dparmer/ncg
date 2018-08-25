from django.db import models
from django.db.models import Q
import csv
from django.conf import settings
import datetime
from bs4 import BeautifulSoup
import requests
import pytz
from django.utils.timezone import get_current_timezone, make_aware
import re
import random
import celery
import celery.result as result


# Create your models here.


class Player(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=30, verbose_name='First Name')
    last_name = models.CharField(max_length=30, verbose_name='Last Name')
    wins = models.IntegerField(verbose_name='Wins')
    losses = models.IntegerField(verbose_name='Losses')
    username = models.CharField(max_length=50, verbose_name='User Name', null=True, blank=True)
    has_current_entry = models.BooleanField(verbose_name='Has Current Entry?', default=False)
    latest_entry_time = models.DateTimeField(verbose_name="Last Entry", null=True, blank=True)
    active_wk_points = models.IntegerField(verbose_name="Current Week Points", default=0)
    last_access = models.DateTimeField(verbose_name='last site access time', null=True, blank=True)

    def __str__(self):
        return '%s %s %s %s' % (self.id, self.last_name, self.first_name, self.username)

    def get_absolute_url(self):
        return str("/confidence/entry/" + str(self.id) + "/" + str(NflGame.get_nfl_week()) + "/")

    def get_update_url(self):
        return str("/confidence/update_entry/" + str(self.id) + "/" + str(NflGame.get_nfl_week()) + "/")

    def set_last_access_time(self):
        now = datetime.datetime.now()
        now = make_aware(now, get_current_timezone(), is_dst=True)
        self.last_access = now
        self.save()

    def set_entry(self):
        self.has_current_entry = True
        now = datetime.datetime.now()
        now = make_aware(now, get_current_timezone(), is_dst=True)
        self.latest_entry_time = now
        self.save()

    def check_entry(self):
        current_nfl_week = NflGame.get_nfl_week()
        latest_entry_week = NflGame.get_nfl_week(self.latest_entry_time)
        print('player', self.username, 'latest-entry', latest_entry_week, 'current nfl wk', current_nfl_week, 'self-entry time', self.latest_entry_time)
        if current_nfl_week != latest_entry_week:
            self.has_current_entry = False
            self.save()

    @property
    def current_points(self):
        week = NflGame.get_nfl_week()
        season = NflGame.get_nfl_season()
        points = Entry.get_points_total(season=season, week=week, player=self)
        self.active_wk_points = points['points']
        self.save()
        return points

    @classmethod
    def get_current_players(cls):

        try:
            players = cls.objects.filter(has_current_entry=True)
            for player in players:
                player.current_points
                player.check_entry()
            return cls.objects.filter(has_current_entry=True).order_by('-active_wk_points')
        except Exception as inst:
            print(inst)
            return None

    @classmethod
    def get_player(cls, username=None, id=None):
        if username:
            try:
                return Player.objects.get(username=username)
            except Exception as inst:
                print("player not found: ", username)
                return None
        elif id:
            try:
                return Player.objects.get(id=id)
            except Exception as inst:
                print("player not found: ", id)
                return None


class NflTeam(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, verbose_name='Team Name')
    city = models.CharField(max_length=30, verbose_name='Team City')
    short_name = models.CharField(max_length=3, verbose_name='Team Short Name')
    wins = models.IntegerField(verbose_name='Wins')
    losses = models.IntegerField(verbose_name='Losses')
    alias = models.CharField(max_length=30, verbose_name='Team Alias', default=None, null=True, blank=True)

    def __str__(self):
        return '%s %s %s' % (self.id, self.city, self.name)

    def get_absolute_url(self):
        return "/confidence/team/%i/" % self.id

    @classmethod
    def get_team(cls, short_name=None, city=None, name=None):
        if short_name:
            try:
                if short_name == 'JAX':
                    short_name = 'JAC'
                if short_name == 'LA':
                    short_name = 'LAR'
                return cls.objects.get(short_name=short_name)
            except Exception as inst:
                print('short_name->', short_name, inst)
                return None
        elif city and name:
            try:
                return cls.objects.get(city=city, name=name)
            except Exception as inst:
                print(inst)
                return None
        elif name:
            try:
                return cls.objects.get(name=name)
            except Exception as inst:
                print(inst)
                return None
        elif city:
            try:
                return cls.objects.get(city=city)
            except Exception as inst:
                try:
                    return cls.objects.get(alias=city)
                except Exception as inst:
                    print(inst)
                    return None
        else:
            print('args not correct')
            return None

    def get_completed_games(self):
        return NflGame.objects.filter(Q(home_team=self) | Q(away_team=self), is_final=True)


class CurrentNflGame(models.Manager):

    def get_queryset(self):
        return super(CurrentNflGame, self).get_queryset().filter(week=NflGame.get_nfl_week()).order_by('game_time', 'id')


class NflGame(models.Model):
    id = models.AutoField(primary_key=True)
    home_team = models.ForeignKey(NflTeam, on_delete=models.CASCADE, related_name='+', verbose_name='Home Team')
    away_team = models.ForeignKey(NflTeam, on_delete=models.CASCADE, related_name='+', verbose_name='Away Team')
    season = models.IntegerField(verbose_name='Season')
    week = models.IntegerField(verbose_name='Week')
    game_date = models.DateField(verbose_name='Game Date')
    game_time = models.DateTimeField(verbose_name='Game Time')
    winner = models.ForeignKey(NflTeam, on_delete=models.CASCADE, related_name='+',
                               verbose_name='Winning Team', blank=True, null=True)
    home_team_score = models.IntegerField(verbose_name='Home Team Score')
    away_team_score = models.IntegerField(verbose_name='Away Team Score')
    is_final = models.BooleanField(verbose_name='Game Complete')
    in_progress = models.BooleanField(verbose_name='Game In Progress', default=False)
    game_status = models.CharField(max_length=15, verbose_name='Game Status', default='Scheduled')
    home_team_line = models.FloatField(verbose_name="Home Team Line", default=0, null=True)
    away_team_line = models.FloatField(verbose_name="Away Team Line", default=0, null=True)
    objects = models.Manager()
    current_games = CurrentNflGame()

    def __str__(self):
        return '%s %s %s %s %s %s' % (self.id, self.game_date,
                                self.home_team.name, self.home_team_line,
                                self.away_team.name, self.away_team_line )

    @property
    def entries(self):
        return Entry.objects.filter(nfl_game=self, week=self.week, season=self.season).order_by('player')

    @property
    def losing_team(self):
        if self.winner == self.home_team:
            return 2
        else:
            return 1

    @property
    def home_team_wline(self):
        if self.home_team_line < 0:
            return self.home_team.name + "(" + str(self.home_team_line) + ")"
        else:
            return self.home_team.name

    @property
    def away_team_wline(self):
        if self.away_team_line < 0:
            return self.away_team.name + "(" + str(self.away_team_line) + ")"
        else:
            return self.away_team.name

    @classmethod
    def is_active_games(cls):
        week = NflGame.get_nfl_week()
        season = NflGame.get_nfl_season()
        is_active = False
        for game in NflGame.objects.filter(season=season, week=week):
            if game.game_status == 'Scheduled' or game.game_status == 'Final':
                print('NflGame: is_active_games = False', game)
                is_active = False
            else:
                print('NflGame: is_active_games = True', game)
                is_active = True
                return is_active
        return is_active

    def get_winner_pretty(self):
        if self.is_final:
            if self.home_team_score > self.away_team_score:
                return str(self.winner.name + " " + str(self.home_team_score) + "-" + str(self.away_team_score))
            else:
                return str(self.winner.name + " " + str(self.away_team_score) + "-" + str(self.home_team_score))
        elif self.in_progress:
            if self.home_team_score > self.away_team_score:
                return str(self.home_team.name + " " + str(self.home_team_score) + "-" + str(self.away_team_score))
            else:
                return str(self.away_team.name + " " + str(self.away_team_score) + "-" + str(self.home_team_score))
        else:
            return "tbd"

    def nfl_game_pretty(self):
        return (self.away_team_wline + " @ " + self.home_team_wline)

    @classmethod
    def get_game_count(cls, week=None):
        season = NflGame.get_nfl_season()
        if not week:
            week = NflGame.get_nfl_week()
        try:
            return cls.objects.filter(season=season, week=week).count()
        except Exception as inst:
            print(inst)
            return None

    @classmethod
    def get_remain_game_count(cls, week=None):
        season = NflGame.get_nfl_season()
        if not week:
            week = NflGame.get_nfl_week()
        try:
            return cls.objects.filter(season=season, week=week, is_final=False, in_progress=False).count()
        except Exception as inst:
            print(inst)
            return None


    def set_result(self, win_score, lose_score, winning_team=None, is_final=False, in_progress=False, status=None):
        self.winner = winning_team
        self.is_final = is_final
        self.in_progress = in_progress
        self.game_status = status

        if winning_team:
            if winning_team == self.home_team:
                self.home_team_score = win_score
                self.away_team_score = lose_score
            else:
                self.home_team_score = lose_score
                self.away_team_score = win_score
            print('NflGame.set_result->', self.winner.name, self.home_team.name, self.away_team.name,
                  self.home_team_score, self.away_team_score)
            self.save()
            print('NflGame.set_result->', self.winner.name, self.home_team.name, self.away_team.name,
                  self.home_team_score, self.away_team_score)
            if is_final:
                for entry in self.entries:
                    entry.set_final(winning_team=winning_team)
        else:
            self.save()

    @classmethod
    def get_nfl_week(cls, today=None):
        tuesdays = [(2018, 9,  4), (2018,  9, 11), (2018,  9, 18), (2018,  9, 25),
                    (2018, 10, 2), (2018, 10, 9), (2018, 10, 16), (2018, 10, 23), (2018, 10, 30),
                    (2018, 11, 6), (2018, 11, 13), (2018, 11, 20), (2018, 11, 27),
                    (2018, 12, 4), (2018, 12, 11), (2018, 12, 18), (2018, 12, 25),
                    (2018, 1,  1), (2018,  1,  8), (2018,  1, 15), (2018,  1, 22)]
        if not today:
            today = pytz.utc.localize(datetime.datetime.now())
        #else:
            #today = pytz.utc.localize(today)

        week = 0
        for tuesday in tuesdays:
            new_week = pytz.utc.localize(datetime.datetime(tuesday[0], tuesday[1], tuesday[2]))
            if today > new_week:
                week += 1
            else:
                return week

    @classmethod
    def get_nfl_season(cls):
        today = datetime.datetime.now()
        if today.month < 3:
            return today.year - 1
        else:
            return today.year

    @classmethod
    def get_game(cls, week=None, home_team=None, away_team=None, id=None):
        if home_team and away_team and week:
            try:
                return NflGame.objects.get(week=week, home_team=home_team, away_team=away_team)
            except Exception as inst:
                """ try reverse in case we do not know home vs away teams  """
                try:
                    return NflGame.objects.get(week=week, home_team=away_team, away_team=home_team)
                except Exception as inst:
                    print(inst)
                    return None
        elif away_team and week:
            try:
                return NflGame.objects.get(week=week, away_team=away_team)
            except Exception as inst:
                print(inst)
                return None
        elif home_team and week:
            try:
                return NflGame.objects.get(week=week, home_team=home_team)
            except Exception as inst:
                print(inst)
                return None
        elif id:
            try:
                return NflGame.objects.get(id=id)
            except Exception as inst:
                print(inst)
                return None
        else:
            print('args incorrect')
            return None


class PlayerEntry(models.Model):
    id = models.AutoField(primary_key=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='+', verbose_name='Player Entry')
    season = models.IntegerField(verbose_name='Season')
    week = models.IntegerField(verbose_name='Week')
    is_active = models.BooleanField(verbose_name="Active Flag")
    points_earned = models.IntegerField(verbose_name='Points Earned', default=0, null=True)
    points_lost = models.IntegerField(verbose_name='Points Lost', default=0, null=True)
    nfl_games_won = models.IntegerField(verbose_name='NFL Games Won', default=0, null=True)
    nfl_games_lost = models.IntegerField(verbose_name='NFL Games Lost', default=0, null=True)

    active_confidence_values = []

    @classmethod
    def create_entry(cls, player, season, week):
        if not PlayerEntry.get_entry(player=player, season=season, week=week):
            pe = PlayerEntry(player=player, season=season, week=week,
                         is_active=True)
            pe.save()
            return pe
        else:
            return None

    def get_entries(self):
            return Entry.get_player_entries(player=self.player, week=self.week)

    @property
    def entries(self):
        return Entry.objects.filter(player=self.player, season=self.season, week=self.week)

    def get_points_earned(self):
        return self.points_earned

    def set_points_earned(self, points):
        self.points_earned += points
        self.nfl_games_won += 1
        self.save()

    def set_points_lost(self, points):
        self.points_lost += points
        self.nfl_games_lost += 1
        self.save()

    @classmethod
    def build_stats(cls):
        for player_entry in cls.objects.all():
            player_entry.points_earned = 0
            player_entry.points_lost = 0
            player_entry.nfl_games_won = 0
            player_entry.nfl_games_lost = 0
            player_entry.save()
            for entry in player_entry.entries:
                if entry.is_complete and entry.is_winner:
                    player_entry.set_points_earned(entry.points_earned)
                elif entry.is_complete and not entry.is_winner:
                    player_entry.set_points_lost(entry.confidence)

    @classmethod
    def get_entry(cls, player, season, week):
        try:
            return cls.objects.get(player=player, week=week, season=season)
        except Exception as inst:
            print(inst)
            return None

    @classmethod
    def build_entry(cls):

        dave = PlayerEntry(player=Player.objects.get(username='dave.parmer'),
                    season=2018,
                    week=13,
                    is_active=True)
        keith = PlayerEntry(player=Player.objects.get(username='keith.parmer'),
                    season=2018,
                    week=13,
                    is_active=True)
        sean = PlayerEntry(player=Player.objects.get(username='sean.parmer'),
                    season=2018,
                    week=13,
                    is_active=True)
        scott = PlayerEntry(player=Player.objects.get(username='scott.parmer'),
                    season=2018,
                    week=13,
                    is_active=True)

        dave.save()
        keith.save()
        sean.save()
        scott.save()


class Entry(models.Model):

    winner_choices = ((1, 'Home Team'), (2, 'Away Team'))

    id = models.AutoField(primary_key=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='+', verbose_name='Player Entry')
    season = models.IntegerField(verbose_name='Season')
    week = models.IntegerField(verbose_name='Week')
    nfl_game = models.ForeignKey(NflGame, on_delete=models.CASCADE, related_name='+', verbose_name='NFL Game')
    is_winner = models.NullBooleanField(verbose_name='Winner', blank=True, null=True)
    confidence = models.IntegerField(verbose_name='Confidence Ranking')
    pick_selection = models.IntegerField(choices=winner_choices, verbose_name='Pick', blank=True, null=True)
    projected_winner = models.ForeignKey(NflTeam, on_delete=models.CASCADE, related_name='+', verbose_name='Projected Winner', blank=True, null=True)
    is_complete = models.BooleanField(verbose_name='Entry Complete', default=False)
    points_earned = models.IntegerField(verbose_name='Points Earned', default=0)
    potential_points = models.IntegerField(verbose_name='Potential Points', default=0)
    is_locked = models.BooleanField(verbose_name="Entry Locked", default=False)

    def __str__(self):
        return '%s %s %s %s %s' % (self.id, self.season, self.week, self.player.last_name, self.player.first_name)

    def set_lock(self):
        #now = pytz.utc.localize(datetime.datetime.now())
        now = datetime.datetime.now()
        print('set_lock now->', now.astimezone(pytz.utc), 'game_time->', self.nfl_game.game_time, 'game->', self.nfl_game)
        if now.astimezone(pytz.utc) > self.nfl_game.game_time:
            print('current time past game time- setting lock', self)
            self.is_locked = True
            self.save()

    @classmethod
    def entry_exists(cls, player, season, week, nfl_game):
        try:
            Entry.objects.get(player=player, week=week, season=season, nfl_game=nfl_game).exists()
            return True
        except Exception as inst:
            print('entry  not found', inst)
            return False

    @classmethod
    def create_entry(cls,player, season, week, nfl_game, confidence, pick_selection, projected_winner, is_locked ):
        if Entry.entry_exists(player=player, season=season, week=week, nfl_game=nfl_game):
            return None
        else:
            e = Entry(player=player, season=season, week=week, nfl_game=nfl_game, is_winner=None,
                      confidence=confidence, pick_selection=pick_selection, projected_winner=projected_winner,
                      is_locked=is_locked)
            e.save()
            return e

    @classmethod
    def create_update_entries(cls, entries, username, mode):
        print("entries->", entries)
        player = Player.get_player(username)

        conf_dict = {}
        pick_dict = {}
        game_dict = {}
        week = NflGame.get_nfl_week()
        season = NflGame.get_nfl_season()

        if mode == 'create':
            try:
                Entry.objects.filter(player=player, season=season, week=week).delete()
            except Exception as inst:
                print("error deleting entries", inst)

            """ shuffle the order so we don't end up with similar rankings"""
            game_count = NflGame.get_game_count()
            remain_game_count = NflGame.get_remain_game_count()
            played_games = game_count - remain_game_count
            conf_range = []

            for count in range(played_games + 1,game_count + 1):
                conf_range.append(count)
            print('conf_range->', conf_range)
            shuff_conf_range = random.sample(conf_range, len(conf_range))
            print('shuffled conf_range->', shuff_conf_range)

            pe = PlayerEntry.create_entry(player=player, season=season, week=week)
            if not pe:
                return {'fail': 'Error- Player Entry exists'}
        else:
            pe = PlayerEntry.get_entry(player=player, week=week, season=season)

        """ build the pick data structures"""
        for key, value in entries.items():
            fld_type, game_id = key.split('_')

            if fld_type == 'pick':
                pick_dict[game_id] = value
                game = NflGame.get_game(id=game_id)
                game_dict[game_id] = game

        conf_complete_game = 0
        conf_index = 0
        print("game_dict->", game_dict)
        for game_id, game in game_dict.items():
            if mode == 'create':
                """ if game over or in progress set to lost and assign lowest confidence """
                if game.is_final or game.in_progress:
                    print("game is final->", game)
                    if game.winner == game.home_team:
                        projected_winner = game.away_team
                    elif game.winner == game.away_team:
                        projected_winner = game.home_team
                    else:
                        projected_winner = None
                    conf_complete_game += 1
                    conf_dict[game_id] = conf_complete_game
                    e = Entry.create_entry(player=player, season=game.season, week=game.week, nfl_game=game,
                                           confidence=int(conf_dict[game_id]), pick_selection=int(pick_dict[game_id]),
                                           projected_winner=projected_winner, is_locked=True)
                    if not e:
                        return {1: "failed to create entry"}
                    print('e->', e.player.first_name, e.id, game.season, game.week, projected_winner.name)
                else: # we can make the pick, game is future game
                    print("game is future->", game)
                    if pick_dict[game_id] == '1':
                        projected_winner = game.home_team
                    elif pick_dict[game_id] == '2':
                        projected_winner = game.away_team
                    else:
                        projected_winner = None
                    conf_dict[game_id] = shuff_conf_range[conf_index]
                    conf_index += 1
                    e = Entry.create_entry(player=player, season=game.season, week=game.week, nfl_game=game,
                                           confidence=int(conf_dict[game_id]), pick_selection=int(pick_dict[game_id]),
                                           projected_winner=projected_winner, is_locked=False)
                    print('e->', e.player.first_name, e.id, game.season, game.week, projected_winner.name)
                    if not e:
                        return {'fail': "failed to create entry"}
            else: # update mode
                try:
                    entry = Entry.get_entry(player=player, season=season, week=week, nfl_game=game)
                except Exception as inst:
                    print('failed to get entry', inst)
                    return {'fail': 'Failed to get entry on update'}

                if pick_dict[game_id] == '1':
                    projected_winner = game.home_team
                elif pick_dict[game_id] == '2':
                    projected_winner = game.away_team
                else:
                    projected_winner = None
                entry.pick_selection = int(pick_dict[game_id])
                entry.projected_winner = projected_winner
                entry.save()

        player.set_entry()
        return { 'success': pe}

    @classmethod
    def set_entry_locks(cls):
        for entry in cls.get_entries(NflGame.get_nfl_week()):
            entry.set_lock()

    @classmethod
    def get_points_total(cls, season, week, player):
        entries = Entry.objects.filter(season=season, week=week, player=player)
        results = {}
        results['points'] = 0
        results['lost_points'] = 0
        results['possible_points'] = 0

        for entry in entries:
            results['points'] += entry.points_earned
            results['possible_points'] += entry.confidence
            if entry.points_earned == 0 and entry.is_complete:
                results['lost_points'] += entry.confidence
        results['remain_points'] = results['possible_points'] - (results['points'] + results['lost_points'])
        return results

    @classmethod
    def get_entries(cls, week, nfl_game=None):
        try:
            if nfl_game:
                return cls.objects.filter(week=week, nfl_game=nfl_game).order_by('player')
            else:
                return cls.objects.filter(week=week).order_by('nfl_game__game_time', 'player')
        except Exception as inst:
            print(inst)
            return None

    @classmethod
    def get_entry(cls, id=None, player=None, season=None, week=None, nfl_game=None):

        if id:
            try:
                print('Entry:get_entry- id:', int(id))
                return cls.objects.get(id=int(id))
            except Exception as inst:
                print('Entry:get_entry- Error:', inst)
                return None
        elif player and season and week and nfl_game:
            try:
                print('Entry:get_entry- input:', player, season, week, nfl_game)
                return cls.objects.get(player=player, season=season, week=week, nfl_game=nfl_game)
            except Exception as inst:
                print('Entry:get_entry- Error:', inst)
                return None

    @classmethod
    def get_player_entries(cls, player, week, sort=None):
        try:
            if sort == 'date':
                return cls.objects.filter(week=week, player=player).order_by("-id")
            else:
                return cls.objects.filter(week=week, player=player).order_by("-confidence")
        except Exception as inst:
            print(inst)
            return None

    @classmethod
    def get_entries_for_game(cls, game):
        week = NflGame.get_nfl_week()
        season = NflGame.get_nfl_season()
        try:
            return cls.objects.filter(nfl_game=game, week=week, season=season, is_complete=False)
        except Exception as inst:
            print(inst)
            return None

    def set_final(self, winning_team):
        if not self.is_complete:
            player_entry = PlayerEntry.objects.get(player=self.player, week=self.week, season=self.season)
            self.is_complete = True
            self.potential_points = 0
            if winning_team == self.projected_winner:
                self.is_winner = True
                self.points_earned = self.confidence
                player_entry.set_points_earned(self.confidence)
            else:
                self.is_winner = False
                self.points_earned = 0
                player_entry.set_points_lost(self.confidence)
            self.save()


class NflTeamMgr(models.Manager):

    @classmethod
    def nfl_team_factory(cls):

        csv_file = settings.DATA_ROOT + '/nfl_teams.csv'
        file_obj = open(csv_file)

        reader = csv.DictReader(file_obj, delimiter=',')
        reader.fieldnames = ['city', 'team', 'shortname']

        for line in reader:
            print(line['team'].strip(), line['city'].strip(), line['shortname'].strip())
            team = NflTeam(name=line['team'].strip(), city=line['city'].strip(),
                           short_name=line['shortname'].strip(), wins=0, losses=0)
            team.save()


class PlayerMgr(models.Manager):

    @classmethod
    def player_factory(cls):

        csv_file = settings.DATA_ROOT + '/players.csv'
        file_obj = open(csv_file)

        reader = csv.DictReader(file_obj, delimiter=',')
        reader.fieldnames = ['firstname', 'lastname']

        for line in reader:
            print(line['firstname'].strip(), line['lastname'].strip())
            player = Player(first_name=line['firstname'].strip(), last_name=line['lastname'].strip(), wins=0, losses=0)
            player.save()


class NflGameMgr(models.Manager):

    result = 0

    @classmethod
    def game_history_update(cls):

        for week in range(1,NflGame.get_nfl_week()):
            cls.game_score_update(week=week)

    @classmethod
    def game_update(cls):

        def parse_teamname(teamnames):
            print(teamnames)
            if len(teamnames) == 3:
                name = teamnames[2]
                city = teamnames[0] + " " + teamnames[1]
            else:
                name = teamnames[1]
                city = teamnames[0]
            return NflTeam.get_team(city=city, name=name)

        csv_file = settings.DATA_ROOT + '/nfl_game_history.csv'
        file_obj = open(csv_file)

        reader = csv.DictReader(file_obj, delimiter=',')
        reader.fieldnames = ['week', 'day', 'date', 'time', 'win_team', 'loc', 'lose_team', 'pts_win',
                             'pts_lose', 'YdsW', 'TOW', 'YdsL', 'TOL']
        for line in reader:
            wteam = parse_teamname(line['win_team'].strip().split())
            lteam = parse_teamname(line['lose_team'].strip().split())
            if line['loc'] == '@':
                home_team = lteam
                away_team = wteam
            else:
                home_team = wteam
                away_team = lteam
            game = NflGame.get_game(week=line['week'], home_team=home_team, away_team=away_team)
            if game:
                game.set_result(winning_team=wteam, win_score=line['pts_win'], lose_score=line['pts_lose'])
            else:
                print('game not found')


    @classmethod
    def game_line_update(cls, week=None):
        footballlocks_com_url = 'http://www.footballlocks.com/nfl_lines.shtml'

        response = requests.get(footballlocks_com_url)
        html = BeautifulSoup(response.content, 'html.parser')
        games_list = []
        columns = html.find_all("td")
        game_data = []
        begin = 0
        count = 0
        for col in columns:
            date_col = re.match( r'(\d+)/(\d+) \d+:\d+ ET', col.text)
            if date_col:
                begin += 1
                count = 0
                continue
            if begin > 0:
                count += 1
                hometeam = re.match(r'At (\D+)', col.text)
                if hometeam:
                    game_data.append(hometeam.group(1))
                else:
                    game_data.append(col.text)
                if count > 3:
                    games_list.append(game_data.copy())
                    game_data.clear()
                    begin = 0

        for game in games_list:
            team1 = NflTeam.get_team(city=game[0])
            team2 = NflTeam.get_team(city=game[2])
            nfl_game = NflGame.get_game(week=NflGame.get_nfl_week(), home_team=team1, away_team=team2)
            if nfl_game:
                if game[1] != 'Off':
                    team1_line = float(game[1])
                    team2_line = abs(float(game[1]))
                else:
                    team1_line = 0
                    team2_line = 0
                if team1 == nfl_game.home_team:
                    nfl_game.home_team_line = team1_line
                    nfl_game.away_team_line = team2_line
                else:
                    nfl_game.home_team_line = team2_line
                    nfl_game.away_team_line = team1_line
                nfl_game.save()
            print("set line-", nfl_game)


    @classmethod
    def game_score_update2(cls, week=None):
        nfl_scores_xml = 'http://www.nfl.com/liveupdate/scorestrip/ss.xml'
        week = NflGame.get_nfl_week()
        season = NflGame.get_nfl_season()
        is_final = False
        response = requests.get(nfl_scores_xml)
        xml = BeautifulSoup(response.content, 'xml')
        games_list = []
        games = xml.find_all("g")
        game_results = {}
        game_list = []
        for game in games:
            fields = str(game).split()
            for field in fields:
                if field.find("=") > 0:
                    key, value = field.split("=")
                    if value[-2:] == "/>":
                        value = value[:len(value)-2]
                    game_results[key] = value.strip('\"')
            game_list.append(game_results.copy())
            game_results.clear()

        print(game_list)

        for game in game_list:
            home_team = NflTeam.get_team(short_name=game['h'])
            away_team = NflTeam.get_team(short_name=game['v'])
            nfl_game = NflGame.get_game(week=week, home_team=home_team, away_team=away_team)

            win_team = None
            if game['q'] == 'P':
                in_progress = False
                is_final = False
                status = 'Scheduled'
            elif game['q'] == 'F' :
                in_progress = False
                is_final = True
                status = 'Final'
            else:
                in_progress = True
                is_final = False
                if 'k' in game:
                    status = 'QTR ' + str(game['q']) + " - " + str(game['k'])
                else:
                    status = 'QTR ' + str(game['q'])
            print('game->', game)
            if int(game['hs']) > int(game['vs']):
                print('home won', game['hs'], '>', game['vs'])
                win_team = home_team
                win_score = game['hs']
                lose_score = game['vs']
            elif int(game['hs']) == int(game['vs']):
                print('tie', game['hs'], '=', game['vs'])
                win_team = None
                win_score = game['hs']
                lose_score = game['vs']
            else:
                print('away won', game['hs'], '<', game['vs'])
                win_team = away_team
                win_score = game['vs']
                lose_score = game['hs']
            if nfl_game:
                nfl_game.set_result(winning_team=win_team, win_score=win_score, lose_score=lose_score, is_final=is_final,
                                in_progress=in_progress, status=status)
                print('game updated->', nfl_game)
            else:
                print('game not found')
            if is_final:
                entries = Entry.get_entries_for_game(nfl_game)
                if entries:
                    for entry in entries:
                        entry.set_final(winning_team=win_team)
        NflGameMgr.game_line_update()


    @classmethod
    def game_score_update(cls, week=None):

        def clean_score(score):
            if score == '--':
                score = 0
                return score
            else:
                score = int(score)
                return score

        if not week:
            week = NflGame.get_nfl_week()

        season = NflGame.get_nfl_season()

        nfl_com_url = 'http://www.nfl.com/scores/' + str(season) + '/REG' + str(week)

        response = requests.get(nfl_com_url)
        html = BeautifulSoup(response.content, 'html.parser')

        div_box_scores = html.find_all("div", attrs={'class':"new-score-box-wrapper"})

        game_dict = {}
        games_list = []
        for box_score in div_box_scores:

            final_c = box_score.find(class_='time-left')
            in_prog_c = final_c.find(class_='down-yardline')

            if not in_prog_c:
                print('game is final', final_c.contents)
                if final_c.contents[0].strip()[:5] == 'FINAL':
                    is_final = True
                    in_progress = False
                    status = 'Final'
                else:
                    is_final = False
                    in_progress = False
                    status = 'Scheduled'

                div_away_team = box_score.find("div", attrs={'class':"away-team"})
                div_home_team = box_score.find("div", attrs={'class':"home-team"})

                home_team_name_class = div_home_team.find(class_='team-name')
                home_team_name_c = home_team_name_class.find('a')
                home_team_score_c = div_home_team.find(class_='total-score')

                away_team_name_class = div_away_team.find(class_='team-name')
                away_team_name_c = away_team_name_class.find('a')
                away_team_score_c = div_away_team.find(class_='total-score')

                home_team_name = home_team_name_c.contents[0].strip()
                away_team_name = away_team_name_c.contents[0].strip()
                print('teams->', home_team_name, away_team_name)
                home_team_score = clean_score(home_team_score_c.contents[0].strip())
                away_team_score = clean_score(away_team_score_c.contents[0].strip())

                home_team = NflTeam.get_team(name=home_team_name)
                away_team = NflTeam.get_team(name=away_team_name)
                game = NflGame.get_game(week=week, home_team=home_team, away_team=away_team)

                win_team = None
                if home_team_score > away_team_score:
                    if is_final:
                        win_team = home_team
                        status = 'Final'
                        in_progress = False
                    win_score = home_team_score
                    lose_score = away_team_score
                else:
                    if is_final:
                        win_team = away_team
                        status = 'Final'
                        in_progress = False
                    win_score = away_team_score
                    lose_score = home_team_score

                if game:
                    game.set_result(winning_team=win_team, win_score=win_score, lose_score=lose_score, is_final=is_final,
                                    in_progress=in_progress, status=status)
                    print('game updated->', game)
                else:
                    print('game not found', game)
                if is_final:
                    entries = Entry.get_entries_for_game(game)
                    if entries:
                        for entry in entries:
                            entry.set_final(winning_team=win_team)

            else:
                print('game in progress', in_prog_c)
                # <span class="down-yardline">1st &amp; 10 IND 19</span>
                is_final = False
                div_away_team = box_score.find("div", attrs={'class':"away-team"})
                div_home_team = box_score.find("div", attrs={'class':"home-team"})

                home_team_name_class = div_home_team.find(class_='team-name')
                home_team_name_c = home_team_name_class.find('a')
                home_team_score_c = div_home_team.find(class_='total-score')

                away_team_name_class = div_away_team.find(class_='team-name')
                away_team_name_c = away_team_name_class.find('a')
                away_team_score_c = div_away_team.find(class_='total-score')

                home_team_name = home_team_name_c.contents[0].strip()
                away_team_name = away_team_name_c.contents[0].strip()
                print('teams->', home_team_name, away_team_name)

                home_team = NflTeam.get_team(name=home_team_name)
                away_team = NflTeam.get_team(name=away_team_name)
                game = NflGame.get_game(week=week, home_team=home_team, away_team=away_team)

                win_team = None

                if game:
                    game.set_result(winning_team=win_team, win_score=0, lose_score=0, is_final=False, in_progress=True)
                    print('game updated->', game)
                else:
                    print('game not found', game)
        NflGameMgr.game_line_update()


    @classmethod
    def game_factory(cls):

        csv_file = settings.DATA_ROOT + '/2018_NFL_Sched.csv'
        file_obj = open(csv_file)

        reader = csv.DictReader(file_obj, delimiter=',')
        reader.fieldnames = ['week', 'game', 'date', 'time', 'away_team', 'home_team']
        season = int(2018)

        for line in reader:
            #print(line['week'].strip(), line['game'].strip(), line['date'].strip(), line['time'].strip(),
            #      line['away_team'].strip(), line['home_team'].strip())
            home_team = NflTeam.get_team(line['home_team'].strip())
            away_team = NflTeam.get_team(line['away_team'].strip())

            dates = line['date'].strip().split('/')
            hour = line['time'].strip().split(':')
            hour_of_day = int(hour[0])
            min_of_day, am_pm = hour[1].split()
            newdate = str(int(dates[2]) + 2000) + "-" + str(dates[0]) + "-" + str(dates[1])
            if am_pm == 'PM':
                hour_of_day += 12

            gametime = datetime.datetime(int(dates[2]) + 2000, int(dates[0]), int(dates[1]),
                                         hour=hour_of_day, minute=int(min_of_day))
            new_york_tz = pytz.timezone("America/New_York")
            gametime = make_aware(gametime, new_york_tz, is_dst=True)
            print('timezone-', get_current_timezone(), 'time-', hour_of_day, min_of_day, 'gametime-', gametime)

            if home_team is None or away_team is None:
                print(line['away_team'].strip(), line['home_team'].strip())
                continue
            else:
                game = NflGame(home_team=home_team,
                               away_team=away_team,
                               season=season,
                               week=int(line['week'].strip()),
                               game_date=newdate,
                               game_time=gametime,
                               winner=None,
                               home_team_score=0,
                               away_team_score=0,
                               is_final=False)
                game.save()

        """ update the game scores """
        cls.game_history_update()


class TaskManager(models.Model):

    id = models.AutoField(primary_key=True)
    task_id = models.CharField(max_length=255, verbose_name='task id for task')
    task_name = models.CharField(max_length=30, verbose_name='task name')

    @classmethod
    def set_id(self, task_id, task_name):
        try:
            print('TaskManager:set_id updating', task_id, task_name)
            t = TaskManager.objects.get(task_name=task_name)
            t.task_id = task_id
            t.save()
            return t
        except Exception as inst:
            try:
                print('TaskManager:set_id creating', task_id, task_name)
                t = TaskManager(task_id=task_id, task_name=task_name)
                t.save()
                return t
            except Exception as inst:
                print('TaskManager:set_id failed', inst)
                return None

    @classmethod
    def get_task_id(cls, task_name):
        try:
            return TaskManager.objects.get(task_name=task_name).task_id
        except Exception as inst:
            print('TaskManager:get_task_id failed', inst)
            return None

    @classmethod
    def get_task(cls, task_name):
        try:
            return TaskManager.objects.get(task_name=task_name)
        except Exception as inst:
            print('TaskManager:get_task_id failed', inst)
            return None

    def status(self):
        task_status = result.AsyncResult(self.task_id)
        print('TaskManager:is_running task_status', task_status.status)
        return task_status.status

    def is_complete(self):
        task_result = result.AsyncResult(id=self.task_id)
        print('TaskManager:is_complete', task_result.ready())
        return task_result.ready()





