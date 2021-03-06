from django.contrib import admin
from .models import Player, NflGame, NflTeam, Entry, NflGameMgr, PlayerEntry


class PlayerAdmin(admin.ModelAdmin):
    fields = ['first_name', 'last_name', 'losses', 'wins', 'username', 'has_current_entry',
              'latest_entry_time', 'active_wk_points', 'last_access']
    list_display = ['id', 'first_name', 'last_name', 'losses', 'wins', 'username',
                    'has_current_entry', 'latest_entry_time', 'active_wk_points', 'last_access']


class NflGameAdmin(admin.ModelAdmin):
    fields = ['home_team', 'away_team', 'home_team_score', 'away_team_score',
              'game_date', 'game_time', 'is_final', 'season', 'week', 'winner']
    list_display = ['id', 'home_team', 'away_team', 'home_team_score', 'away_team_score',
                    'game_date', 'game_time', 'is_final', 'season', 'week', 'winner']

    def load_games_from_file(self, request, queryset):
        NflGameMgr.game_factory()
    load_games_from_file.short_description = "Load Games From File"
    #actions = ['load_games_from_file']

    def load_results_from_file(self, request, queryset):
        NflGameMgr.game_update()
    load_results_from_file.short_description = "Load Game Results From File"
    actions = ['load_games_from_file', 'load_results_from_file']


class NflTeamAdmin(admin.ModelAdmin):
    fields = ['city', 'name', 'short_name', 'wins', 'losses', 'alias' ]
    list_display = ['id', 'name', 'short_name', 'wins', 'losses', 'alias']


class EntryAdmin(admin.ModelAdmin):
    fields = ['player', 'season', 'week', 'nfl_game', 'is_winner',
              'confidence', 'pick_selection', 'projected_winner', 'is_complete', 'points_earned',
              'potential_points', 'is_locked' ]
    list_display = ['id', 'player', 'season', 'week', 'nfl_game', 'is_winner',
                    'confidence', 'pick_selection', 'projected_winner', 'is_complete', 'points_earned',
                    'potential_points', 'is_locked']

class PlayerEntryAdmin(admin.ModelAdmin):
    fields = ['player', 'season', 'week', 'is_active', 'points_earned',
              'points_lost', 'nfl_games_won', 'nfl_games_lost' ]
    list_display = ['id', 'player', 'season', 'week', 'is_active', 'points_earned',
              'points_lost', 'nfl_games_won', 'nfl_games_lost' ]

admin.site.register(Player, PlayerAdmin)
admin.site.register(NflGame, NflGameAdmin)
admin.site.register(NflTeam, NflTeamAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(PlayerEntry, PlayerEntryAdmin)