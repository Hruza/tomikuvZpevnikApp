from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import generic
from django.urls import reverse
from .models import Song
from random import choice
from tomikuvzpevnik.forms import SongEditForm
from tomikuvzpevnik.song_utils.conversions import ultimate_to_base
import locale
from .forms import AddSongForm

class IndexView(generic.ListView):
    model = Song
    ordering = ['title']
    template_name = "tomikuvzpevnik/index.html"
    context_object_name = "song_list"

    def get_queryset(self):
        # Fetch all songs from the database
        songs = Song.objects.all()
        # Set the locale to use for sorting (e.g., 'en_US.UTF-8')
        locale.setlocale(locale.LC_ALL, 'cs_CZ.UTF-8')
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
        # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = AddSongForm(request.POST)

        if form.is_valid():
            # check whether it's valid:
            song_data = ultimate_to_base(form.cleaned_data['song_url'])
            if not song_data is None:
                request.session['unsaved_song_data'] = song_data
                return redirect(reverse("tomikuvzpevnik:song_edit", args=(0,)))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AddSongForm()

    return render(request, "tomikuvzpevnik/addSong.html", {"form": form})


@login_required
def edit_song(request, pk):
    if pk == 0:
        song_data = request.session.get('unsaved_song_data', None)
        song = Song(**song_data,owner=request.user) 
    else:
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

    return render(request, "tomikuvzpevnik/editSong.html", {'form': form, 'song': song})