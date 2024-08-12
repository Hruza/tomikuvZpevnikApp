from django.urls import path

from . import views

app_name = "tomikuvzpevnik"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("song/<int:pk>/", views.SongPageView.as_view(), name="song_page"),
    path("song/<int:pk>/edit/", views.SongEditView.as_view(), name="song_edit"),
    path("song/add/", views.SongEditView.as_view(), name="song_edit"),
]