from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views import generic
from .models import Song


class IndexView(generic.ListView):
    model = Song
    template_name = "tomikuvzpevnik/index.html"
    context_object_name = "song_list"

class SongPageView(generic.DetailView):
    model = Song
    template_name = "tomikuvzpevnik/viewSong.html"
    context_object_name = "song"

class SongEditView(generic.DetailView):
    model = Song
    template_name = "tomikuvzpevnik/editSong.html"
    context_object_name = "song"

@login_required
def add_song(request):
    return render(request, 'edit_song.html')


@login_required
def edit_song(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    
    # Check if the current user is either the song owner or in the 'Song Admins' group
    if song.user != request.user and not request.user.groups.filter(name='Song Admins').exists():
        return redirect('song_detail', song_id=song.id)  # Redirect if not authorized

    if request.method == 'POST':
        song.title = request.POST['title']
        song.artist = request.POST['artist']
        song.lyrics = request.POST['lyrics']
        song.chords = request.POST['chords']
        song.save()
        return redirect('song_detail', song_id=song.id)

    return render(request, 'edit_song.html', {'song': song})