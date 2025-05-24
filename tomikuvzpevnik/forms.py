from django.forms import ModelForm
from django import forms
from tomikuvzpevnik.models import Song
from django.core.exceptions import ValidationError
from urllib.parse import urlparse

def validate_no_html(value):
    if '<' in value or '>' in value:
        raise ValidationError(
            f'Invalid characters in use: ">" or "<"',
            code='invalid'
        )

def validate_url(value):
    if value.strip() == "":
        return
    else:
        parsed_url = urlparse(value)
        hostname = str(parsed_url.netloc)
        if not hostname.endswith("ultimate-guitar.com"):
            raise ValidationError("URL musí být ze stránky 'ultimate-guitar.com'")

class AddSongForm(forms.Form):
    song_url = forms.URLField(label='Zadej URL z ultimate-guitar.com', max_length=200, required=False, validators=[validate_url])
            

class SongEditForm(ModelForm):
    title = forms.CharField(max_length=200,validators=[validate_no_html])
    artist = forms.CharField(max_length=200,validators=[validate_no_html])
    lyrics = forms.CharField(widget=forms.Textarea, validators=[validate_no_html])
    capo = forms.IntegerField(min_value=0,max_value=11, label="Capo", initial=0)

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
