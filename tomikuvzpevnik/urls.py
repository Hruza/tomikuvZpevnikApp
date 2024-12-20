from django.urls import path

from . import views

app_name = "tomikuvzpevnik"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("song/<int:pk>/", views.SongPageView.as_view(), name="song_page"),
    path("song/<int:pk>/update/", views.update_song_data, name="song_update"),
    path("song/<int:pk>/edit/", views.edit_song, name="song_edit"),
    path("song/<int:pk>/delete/", views.delete_song, name="song_delete"),
    path("song/add/", views.add_song, name="song_add"),
    path("song/random/", views.get_random_song, name="song_random"),
]