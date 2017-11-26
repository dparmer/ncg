from django.forms import ModelForm, forms, ChoiceField, Select, IntegerField, NumberInput, HiddenInput, CharField
from .models import Entry, NflGame, Player


class EntryUpdateForm(ModelForm):

    class Meta:
        model = Entry
        fields = ()

    def __init__(self, *args, **kwargs):
        player_id = kwargs.pop('player_id', None)
        week = kwargs.pop('week', None)
        super(EntryUpdateForm, self).__init__(*args, **kwargs)
        print("EntryUpdateForm kwargs->", player_id, week )
        entries = Entry.get_player_entries(player=Player.get_player(id=player_id), week=week)

        for entry in entries:
            if entry.is_locked:
                self.fields.update({'pick_' + str(entry.nfl_game.id): ChoiceField(widget = Select(), choices = ([(0,'None'),(1,entry.nfl_game.home_team.name), (2,entry.nfl_game.away_team.name), ]), initial=entry.pick_selection, disabled=True ) })
                self.fields.update({'confidence_' + str(entry.nfl_game.id): IntegerField(widget = NumberInput(), initial=entry.confidence, disabled=True )  })
            else:
                self.fields.update({'pick_' + str(entry.nfl_game.id): ChoiceField(widget = Select(), choices = ([(0,'None'),(1,entry.nfl_game.home_team.name), (2,entry.nfl_game.away_team.name), ]), initial=entry.pick_selection ) })
                self.fields.update({'confidence_' + str(entry.nfl_game.id): IntegerField(widget = NumberInput(), initial=entry.confidence )  })

    def clean(self):
        cleaned_data=super(EntryUpdateForm, self).clean()
        values = []
        val_dict = {}
        for key, value in cleaned_data.items():
            fld_type, game_id = key.split('_')
            if fld_type == 'confidence':
                values.append(value)

                print('value->', value, 'val-dict->', val_dict)
                if value in val_dict:
                    print('val in val_dict')
                    raise forms.ValidationError("Confidence values must be unique")

                val_dict[value] = 1

        values.sort()
        if values[len(values)-1] - values[0] + 1 != len(values):
            raise forms.ValidationError("Confidence values must be consecutive")



class EntryAddForm(ModelForm):

    class Meta:
        model = Entry
        fields = ()

    def __init__(self, *args, **kwargs):
        super(EntryAddForm, self).__init__(*args, **kwargs)
        cnt = 0
        for game in NflGame.current_games.all():
            self.fields.update({'pick_' + str(game.id): ChoiceField(widget = Select(), choices = ([(0,'None'),(1,game.home_team.name), (2,game.away_team.name), ]), initial=0 ) })
            self.fields.update({'confidence_' + str(game.id): IntegerField(widget = NumberInput(), initial=0 )  })

    def clean(self):
        cleaned_data=super(EntryAddForm, self).clean()
        values = []
        val_dict = {}
        for key, value in cleaned_data.items():
            fld_type, game_id = key.split('_')
            if fld_type == 'confidence':
                values.append(value)

                print('value->', value, 'val-dict->', val_dict)
                if value in val_dict:
                    print('val in val_dict')
                    raise forms.ValidationError("Confidence values must be unique")

                val_dict[value] = 1

        values.sort()
        if values[len(values)-1] - values[0] + 1 != len(values):
            raise forms.ValidationError("Confidence values must be consecutive")

