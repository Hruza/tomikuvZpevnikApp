from django.db import models
from django.contrib.auth.models import User

class Song(models.Model):
    title = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # Each song is owned by a user
    artist = models.CharField(max_length=200)
    capo = models.IntegerField()
    lyrics = models.TextField()

    def __str__(self):
        return f"{self.title} by {self.artist}"
