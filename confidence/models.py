from django.db import models
from django.db.models import Q
import csv
from django.conf import settings
import datetime
from bs4 import BeautifulSoup
import requests
import pytz
from django.utils.timezone import get_current_timezone, make_aware


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

    def __str__(self):
        return '%s %s %s %s' % (self.id, self.last_name, self.first_name, self.username)

    def get_absolute_url(self):
        return str("/confidence/entry/" + str(self.id) + "/" + str(NflGame.get_nfl_week()) + "/")

    def get_update_url(self):
        return str("/confidence/update_entry/" + str(self.id) + "/" + str(NflGame.get_nfl_week()) + "/")


    def set_entry(self):
        self.has_current_entry = True

        now = datetime.datetime.now()
        now = make_aware(now, get_current_timezone(), is_dst=True)
        self.latest_entry_time = now
        self.save()

    def check_entry(self):
        current_nfl_week = NflGame.get_nfl_week()
        latest_entry_week = NflGame.get_nfl_week(self.latest_entry_time)
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

    def __str__(self):
        return '%s %s %s' % (self.id, self.city, self.name)

    def get_absolute_url(self):
        return "/confidence/team/%i/" % self.id

    @classmethod
    def get_team(cls, short_name=None, city=None, name=None):
        if short_name:
            try:
                return cls.objects.get(short_name=short_name)
            except Exception as inst:
                print(inst)
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
        else:
            print('args not correct')
            return None

    def get_completed_games(self):
        return NflGame.objects.filter(Q(home_team=self) | Q(away_team=self), is_final=True)


class CurrentNflGame(models.Manager):

    def get_queryset(self):
        return super(CurrentNflGame, self).get_queryset().filter(week=NflGame.get_nfl_week()).order_by('game_time')


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
    objects = models.Manager()
    current_games = CurrentNflGame()

    def __str__(self):
        return '%s %s %s %s' % (self.id, self.game_date, self.home_team.name, self.away_team.name)

    @property
    def losing_team(self):
        if self.winner == self.home_team:
            return 2
        else:
            return 1

    def get_winner_pretty(self):
        if self.is_final:
            if self.home_team_score > self.away_team_score:
                return str(self.winner.name + " " + str(self.home_team_score) + "-" + str(self.away_team_score))
            else:
                return str(self.winner.name + " " + str(self.away_team_score) + "-" + str(self.home_team_score))
        else:
            return "tbd"

    def nfl_game_pretty(self):
        return (self.away_team.name + " @ " + self.home_team.name)

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


    def set_result(self, win_score, lose_score, winning_team=None, is_final=False, in_progress=False):
        self.winner = winning_team
        if winning_team == self.home_team:
            self.home_team_score = win_score
            self.away_team_score = lose_score
        else:
            self.home_team_score = lose_score
            self.away_team_score = win_score
        self.is_final = is_final
        self.in_progress = in_progress
        if is_final:
            self.game_status = 'Final'
        elif in_progress:
            self.game_status = 'In Progress'
        self.save()

    @classmethod
    def get_nfl_week(cls, today=None):
        tuesdays = [(2017, 9,  5), (2017,  9, 12), (2017,  9, 19), (2017,  9, 26),
                    (2017, 10, 3), (2017, 10, 10), (2017, 10, 17), (2017, 10, 24), (2017, 10, 31),
                    (2017, 11, 7), (2017, 11, 14), (2017, 11, 21), (2017, 11, 28),
                    (2017, 12, 5), (2017, 12, 12), (2017, 12, 19), (2017, 12, 26),
                    (2018, 1,  2), (2018,  1,  9), (2018,  1, 16), (2018,  1, 23)]
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

    active_confidence_values = []

    def get_entries(self):
            return Entry.get_player_entries(player=self.player, week=self.week)

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
                    season=2017,
                    week=13,
                    is_active=True)
        keith = PlayerEntry(player=Player.objects.get(username='keith.parmer'),
                    season=2017,
                    week=13,
                    is_active=True)
        sean = PlayerEntry(player=Player.objects.get(username='sean.parmer'),
                    season=2017,
                    week=13,
                    is_active=True)
        scott = PlayerEntry(player=Player.objects.get(username='scott.parmer'),
                    season=2017,
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
    def get_entries(cls, week):
        try:
            return cls.objects.filter(week=week)
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
    def get_player_entries(cls, player, week):
        try:
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
            self.is_complete = True
            self.potential_points = 0
            if winning_team == self.projected_winner:
                self.is_winner = True
                self.points_earned = self.confidence
            else:
                self.is_winner = False
                self.points_earned = 0
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
                else:
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
                home_team_score = clean_score(home_team_score_c.contents[0].strip())
                away_team_score = clean_score(away_team_score_c.contents[0].strip())

                home_team = NflTeam.get_team(name=home_team_name)
                away_team = NflTeam.get_team(name=away_team_name)
                game = NflGame.get_game(week=week, home_team=home_team, away_team=away_team)

                win_team = None
                if home_team_score > away_team_score:
                    if is_final:
                        win_team = home_team
                    win_score = home_team_score
                    lose_score = away_team_score
                else:
                    if is_final:
                        win_team = away_team
                    win_score = away_team_score
                    lose_score = home_team_score

                if game:
                    game.set_result(winning_team=win_team, win_score=win_score, lose_score=lose_score, is_final=is_final)
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


    @classmethod
    def game_factory(cls):

        csv_file = settings.DATA_ROOT + '/2017_NFL_Sched.csv'
        file_obj = open(csv_file)

        reader = csv.DictReader(file_obj, delimiter=',')
        reader.fieldnames = ['week', 'game', 'date', 'time', 'away_team', 'home_team']
        season = int(2017)

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


