from django.db import models
from django.contrib.auth.models import User
from tomikuvzpevnik.song_utils.conversions import base_to_html
from django.utils.html import strip_tags
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import datetime

class Song(models.Model):
    title = models.CharField(max_length=200)
    # Each song is owned by a user
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    artist = models.CharField(max_length=200)
    capo = models.IntegerField()
    lyrics = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.artist}"

    def get_html_text(self):
        return base_to_html(strip_tags(self.lyrics))

    def isEditable(self, user: User):
        return (
            user.is_authenticated
            and user == self.owner
            or user.groups.filter(name="Song Admins").exists()
        )

    def isFavorite(self, user: User):
        return (
            user.is_authenticated
            and user == self.owner
            or user.groups.filter(name="Song Admins").exists()
        )


def validate_capo(value):
    if value % 2 != 0:
        raise ValidationError(
            _("%(value)s has to be a value between -11 and 11"),
            code="invalid",
            params={"value": value},
        )


class SongData(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    favorite = models.BooleanField(default=False)
    transpose = models.IntegerField(default=0, validators=[validate_capo])

    class Meta:
        unique_together = ("user", "song")


class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dark_theme = models.BooleanField(default=False)
