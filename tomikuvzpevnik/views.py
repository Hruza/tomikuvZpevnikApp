from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.utils.decorators import method_decorator
from django.views import generic
from django.db.models.functions import Collate
from django.http import HttpRequest, JsonResponse
from django.urls import reverse
from .models import Song, SongData, UserPreferences
from random import choice, choices
from tomikuvzpevnik.forms import SongEditForm
from tomikuvzpevnik.song_utils.conversions import ultimate_to_base
from django.db.models import BooleanField, ExpressionWrapper, Q, Subquery, OuterRef
import locale
from .forms import AddSongForm

class IndexView(generic.ListView):
    model = Song
    ordering = ["title"]
    template_name = "tomikuvzpevnik/index.html"
    context_object_name = "song_list"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            favorite_subquery = SongData.objects.filter(
                user=self.request.user, song=OuterRef("pk"), favorite=True
            ).values("favorite")[:1]

            # Add the information about being favorite
            songs = (
                Song.objects.select_related("owner")
                .only("title", "artist", "owner__username")
                .annotate(
                    favorite=Subquery(favorite_subquery, output_field=BooleanField())
                )
            )
        else:
            # Fetch all songs from the database
            songs = (
                Song.objects.select_related("owner")
                .only("title", "artist", "owner__username")
                .all()
            )
        # Sort songs using locale-aware sorting
        sort_by = self.request.GET.get("sort", "name")
        ascending = not self.request.GET.get("order", "1") == "-1"

        if sort_by in ["created", "last_modified"]:
            prefix = "" if ascending else "-"
            songs = songs.order_by(prefix + sort_by)
        else:   
            songs = songs.order_by(Collate("title", "CZECH_NOCASE"))
        return songs


class SongPageView(generic.DetailView):
    model = Song
    template_name = "tomikuvzpevnik/viewSong.html"
    context_object_name = "song"

    def get_queryset(self):
        song_fields = [f.name for f in Song._meta.get_fields()]
        return (
            Song.objects.select_related("owner")
            .only(*song_fields, "owner__username")
            .all()
        )

    def get_object(self):
        self.pk_url_kwarg
        self.song = super().get_object()
        return self.song

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        song = self.song
        user = self.request.user
        context["editable"] = song.isEditable(user)

        song_data = None
        if user.is_authenticated:
            song_data = SongData.objects.filter(user=user, song=song).first()

        context["song_data"] = song_data
        rng_mode = self.request.GET.get("rng_mode", "0")
        if not rng_mode in {"0", "1", "2"}:
            rng_mode = "0"
        context["rng_mode"] = rng_mode
        return context


def get_random_song(request:HttpRequest):
    rng_mode = request.GET.get("rng_mode", "0")
    random_pk = None
    if request.user.is_authenticated and rng_mode == "1":
        FAVORITE_WEIGHTING = 10
        favorites = SongData.objects.filter(user=request.user, favorite=True)
        pks = Song.objects.values_list("pk", flat=True)
        if len(favorites) > 0:
            favorite_keys = {sd.song.pk for sd in favorites}
            weights = [FAVORITE_WEIGHTING if pk in favorite_keys else 1 for pk in pks]
            random_pk = choices(pks, weights)[0]
    elif request.user.is_authenticated and rng_mode == "2":
        favorites = SongData.objects.filter(user=request.user, favorite=True)
        if len(favorites) > 0:
            random_pk = choice(favorites).song.pk

    if random_pk is None:
        pks = Song.objects.values_list("pk", flat=True)
        random_pk = choice(pks)
    query = f"?rng_mode={rng_mode}" if rng_mode in {"1", "2"} else ""
    return redirect(reverse("tomikuvzpevnik:song_page", args=(random_pk,)) + query)


@login_required
def add_song(request:HttpRequest):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = AddSongForm(request.POST)

        if form.is_valid():
            # check whether it's valid:
            if form.cleaned_data['song_url'].strip() == "":
                request.session['unsaved_song_data'] = {}
                return redirect(reverse("tomikuvzpevnik:song_edit", args=(0,)))
            song_data = ultimate_to_base(form.cleaned_data['song_url'])
            if not song_data is None:
                request.session['unsaved_song_data'] = song_data
                return redirect(reverse("tomikuvzpevnik:song_edit", args=(0,)))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AddSongForm()

    return render(request, "tomikuvzpevnik/addSong.html", {"form": form})


@login_required
def update_song_data(request: HttpRequest, pk: int):
    if (
        request.method == "POST"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"  # is AJAX
    ):
        song = get_object_or_404(Song, id=pk)
        song_data, _ = SongData.objects.get_or_create(user=request.user, song=song)

        # Parse AJAX request values
        if not "favorite" in request.POST.keys():
            return JsonResponse({"success": False}, status=400)

        favorite_value = request.POST.get("favorite") == "true"

        # song_data.rating = int(rating_value)
        song_data.favorite = favorite_value
        song_data.save()
        print(song_data.favorite)
        song_data_dict = {
            f.name: str(song_data.__getattribute__(f.name))
            for f in song_data._meta.get_fields()
        }

        # Return JSON response with current song_data values
        return JsonResponse({"success": True} | song_data_dict)

    return JsonResponse({"success": False}, status=400)


@login_required
def edit_song(request:HttpRequest, pk:int):
    if pk == 0:
        song_data = request.session.get('unsaved_song_data', None)
        song = Song(**song_data,owner=request.user) 
    else:
        song = get_object_or_404(Song, id=pk)
    
    if not song.isEditable(request.user):
        return redirect(reverse("tomikuvzpevnik:song_page", args=(pk,)))  # Redirect if not authorized

    if request.method == 'POST':
        form = SongEditForm(request.POST, instance=song)
        if form.is_valid():
            new_song = form.save()
            return redirect(reverse("tomikuvzpevnik:song_page", args=(new_song.pk,)))
    else:
        form = SongEditForm(instance=song)

    return render(request, "tomikuvzpevnik/editSong.html", {'form': form, 'song': song})

@login_required
def delete_song(request:HttpRequest, pk:int):
    song = get_object_or_404(Song, id=pk)

    if song.owner != request.user and not request.user.groups.filter(name="Song Admins").exists():
        print(f"User {request.user.username} attempted to delete a song '{song.name}' without sufficient rights.")
        return redirect(reverse("tomikuvzpevnik:song_edit", args=(pk,)))  # Redirect if not authorized

    if request.method == 'POST':
        print(f"Removing song {song.title}...")
        song.delete()
        return redirect(reverse("tomikuvzpevnik:index"))


def register(request: HttpRequest):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False) 
            user.is_active = False
            user.save()
            # send_verification_email(request, user)
            # messages.success(request, _('Please check your email to verify your account.'))
            return redirect('login') 
    else:
        form = UserCreationForm()

    return render(request, 'registration/create_account.html', {'form': form})
