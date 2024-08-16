from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import generic
from django.urls import reverse
from .models import Song
from random import choice
from tomikuvzpevnik.forms import SongEditForm 
import locale

class IndexView(generic.ListView):
    model = Song
    ordering = ['title']
    template_name = "tomikuvzpevnik/index.html"
    context_object_name = "song_list"

    def get_queryset(self):
        # Fetch all songs from the database
        songs = Song.objects.all()
        # Set the locale to use for sorting (e.g., 'en_US.UTF-8')
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        # Sort songs using locale-aware sorting
        return sorted(songs, key=lambda song: locale.strxfrm(song.title))

class SongPageView(generic.DetailView):
    model = Song
    template_name = "tomikuvzpevnik/viewSong.html"
    context_object_name = "song"

def get_random_song(request):
    pks = Song.objects.values_list("pk", flat=True)
    random_pk = choice(pks)
    return redirect(reverse("tomikuvzpevnik:song_page", args=(random_pk,)))


@login_required
def add_song(request):
    return render(request, "edit_song.html")


@login_required
def edit_song(request, pk):
    song = get_object_or_404(Song, id=pk)
    
    if song.owner != request.user and not request.user.groups.filter(name="Song Admins").exists():
        return redirect(reverse("tomikuvzpevnik:song_page", args=(pk,)))  # Redirect if not authorized

    if request.method == 'POST':
        form = SongEditForm(request.POST, instance=song)
        if form.is_valid():
            form.save()
            return redirect(reverse("tomikuvzpevnik:song_page", args=(pk,)))
    else:
        form = SongEditForm(instance=song)

    return render(request, "tomikuvzpevnik/editSong.html", {'form': form})