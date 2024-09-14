from django.forms import ModelForm
from django import forms
from tomikuvzpevnik.models import Song
from django.core.exceptions import ValidationError

def validate_no_html(value):
    if '<' in value or '>' in value:
        raise ValidationError(
            f'Invalid characters in use: ">" or "<"',
            code='invalid'
        )

class AddSongForm(forms.Form):
    song_url = forms.URLField(label="Song URL", max_length=200) 

class SongEditForm(ModelForm):
    title = forms.CharField(max_length=200,validators=[validate_no_html])
    artist = forms.CharField(max_length=200,validators=[validate_no_html])
    lyrics = forms.CharField(widget=forms.Textarea, validators=[validate_no_html])

    class Meta:
        model = Song
        fields = ["title", "artist", "capo", "lyrics"]
        labels = {
            "title":"Název písničky",
            "artist":"Autor/Interpret",
            "capo":"Capo:",
            "lyrics":"Text písně:",
        }
        #help_texts = {
        #    "name": _("Some useful help text."),
        #}
