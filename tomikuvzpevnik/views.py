import logging
from random import choice, choices

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import BooleanField, OuterRef, Subquery
from django.db.models.functions import Collate
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import generic

from tomikuvzpevnik.forms import SongEditForm
from tomikuvzpevnik.song_utils.conversions import base_to_tex, ultimate_to_base

from .forms import AddSongForm, UserRegistrationForm
from .models import Song, SongData
from .tokens import account_activation_token

logger = logging.getLogger("tomikuvzpevnik")

FAVORITE_WEIGHTING = 10


class IndexView(generic.ListView):
    model = Song
    ordering = ["title"]
    template_name = "tomikuvzpevnik/index.html"
    context_object_name = "song_list"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            favorite_subquery = SongData.objects.filter(user=self.request.user, song=OuterRef("pk"), favorite=True).values("favorite")[:1]

            # Add the information about being favorite
            songs = Song.objects.select_related("owner").only("title", "artist", "owner__username").annotate(favorite=Subquery(favorite_subquery, output_field=BooleanField()))
        else:
            # Fetch all songs from the database
            songs = Song.objects.select_related("owner").only("title", "artist", "owner__username").all()
        # Sort songs using locale-aware sorting
        sort_by = self.request.GET.get("sort", "name")
        ascending = self.request.GET.get("order", "1") != "-1"

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
        return Song.objects.select_related("owner").only(*song_fields, "owner__username").all()

    def get_object(self, queryset=None):
        self.song = super().get_object(queryset)
        return self.song

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        song = self.song
        user = self.request.user
        context["editable"] = song.isEditable(user)
        logger.info("User %s accessed song page for '%s' (ID: %s). Editable: %s", user.username or "(Anonymous)", song.title, song.pk, context["editable"])
        song_data = None
        if user.is_authenticated:
            song_data = SongData.objects.filter(user=user, song=song).first()

        context["song_data"] = song_data
        rng_mode = self.request.GET.get("rng_mode", "0")
        if rng_mode not in {"0", "1", "2"}:
            rng_mode = "0"
        context["rng_mode"] = rng_mode
        return context


def get_random_song(request: HttpRequest):
    rng_mode = request.GET.get("rng_mode", "0")
    random_pk = None
    if request.user.is_authenticated and rng_mode == "1":
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
def add_song(request: HttpRequest):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = AddSongForm(request.POST)

        if form.is_valid():
            # check whether it's valid:
            if form.cleaned_data["song_url"].strip() == "":
                request.session["unsaved_song_data"] = {}
                logger.info("User %s submitted empty song URL for adding a new song.", request.user.username or "(Anonymous)")
                return redirect(reverse("tomikuvzpevnik:song_edit", args=(0,)))
            song_data = ultimate_to_base(form.cleaned_data["song_url"])
            logger.info("User %s submitted a song URL for adding a new song. URL: %s", request.user.username or "(Anonymous)", form.cleaned_data["song_url"])
            if song_data is not None:
                request.session["unsaved_song_data"] = song_data
                return redirect(reverse("tomikuvzpevnik:song_edit", args=(0,)))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AddSongForm()

    return render(request, "tomikuvzpevnik/addSong.html", {"form": form})


@login_required
def update_song_data(request: HttpRequest, pk: int):
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":  # is AJAX
        song = get_object_or_404(Song, id=pk)
        song_data, _ = SongData.objects.get_or_create(user=request.user, song=song)

        # Parse AJAX request values
        if "favorite" not in request.POST:
            return JsonResponse({"success": False}, status=400)

        favorite_value = request.POST.get("favorite") == "true"

        song_data.favorite = favorite_value
        song_data.save()
        logger.debug("Song favorite status updated: User: %s, Song: %s (ID: %s), Favorite: %s", request.user.username or "(Anonymous)", song.title, song.pk, song_data.favorite)
        song_data_dict = {f.name: str(song_data.__getattribute__(f.name)) for f in song_data._meta.get_fields()}

        # Return JSON response with current song_data values
        return JsonResponse({"success": True} | song_data_dict)

    return JsonResponse({"success": False}, status=400)


@login_required
def edit_song(request: HttpRequest, pk: int):
    if pk == 0:
        song_data = request.session.get("unsaved_song_data", None)
        if song_data is None:
            logger.warning("User %s attempted to edit a new song without providing song data in the session.", request.user.username or "(Anonymous)")
            return redirect(reverse("tomikuvzpevnik:index"))
        song = Song(**song_data, owner=request.user)
    else:
        song = get_object_or_404(Song, id=pk)

    if not song.isEditable(request.user):
        logger.warning("Unauthorized attempt to edit song: User: %s, Song: %s (ID: %s)", request.user.username or "(Anonymous)", song.title, song.pk)
        return redirect(reverse("tomikuvzpevnik:song_page", args=(pk,)))  # Redirect if not authorized

    if request.method == "POST":
        form = SongEditForm(request.POST, instance=song)
        if form.is_valid():
            new_song = form.save()
            logger.info("Song saved: User: %s, Song: %s (ID: %s)", request.user.username or "(Anonymous)", new_song.title, new_song.pk)
            return redirect(reverse("tomikuvzpevnik:song_page", args=(new_song.pk,)))
    else:
        form = SongEditForm(instance=song)

    return render(request, "tomikuvzpevnik/editSong.html", {"form": form, "song": song})


@login_required
def delete_song(request: HttpRequest, pk: int):
    song = get_object_or_404(Song, id=pk)

    if song.owner != request.user and not request.user.groups.filter(name="Song Admins").exists():
        messages.error(request, "Nemáte oprávnění smazat tuto píseň.")
        return redirect(reverse("tomikuvzpevnik:song_edit", args=(pk,)))  # Redirect if not authorized

    if request.method == "POST":
        song.delete()
        messages.success(request, "Píseň byla úspěšně smazána.")
        logger.info("Song deleted: User: %s, Song: %s (ID: %s)", request.user.username or "(Anonymous)", song.title, song.pk)
        return redirect(reverse("tomikuvzpevnik:index"))

    return redirect(reverse("tomikuvzpevnik:song_page", args=(pk,)))


def register(request: HttpRequest):
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect("login")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save the user with is_active=False initially
                    user = form.save(commit=False)
                    user.is_active = False  # Account is inactive until email is verified

                    # Check if the email is already used by another account
                    if User.objects.filter(email=user.email).exists():
                        messages.error(request, "Tento email již je používán jiným účtem.")
                        return render(request, "registration/create_account.html", {"form": form})

                    # Check if a user with the same name already exists
                    if User.objects.filter(username=user.username).exists():
                        messages.error(request, "Tento uživatelské jméno již je používáno jiným účtem.")
                        return render(request, "registration/create_account.html", {"form": form})

                    user.save()

                    mail_subject = "Tomíkův Zpěvník: aktivace účtu"
                    current_site = get_current_site(request)
                    to_email = form.cleaned_data.get("email")
                    message = render_to_string(
                        "registration/account_activation_email.html",
                        {
                            "user": user,
                            "domain": current_site.domain,
                            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                            "token": account_activation_token.make_token(user),
                        },
                    )
                    email = EmailMessage(mail_subject, message, to=[to_email])
                    email.content_subtype = "html"
                    email.send()
                messages.success(request, "Odkaz pro aktivaci účtu byl odeslán na váš email. Pro aktivaci účtu klikněte na odkaz v emailu.")
                logger.info("New user registered: %s (ID: %s). Activation email sent to %s.", user.username, user.pk, to_email)
                return redirect("login")  # Redirect to login page after successful registration
            except Exception:
                # If email sending fails, the transaction rolls back, so user is not created
                messages.error(request, "Nastala chyba při odesílání emailu. Zkuste to prosím znovu později.")
                # Log the error for debugging
                logger.exception("Failed to send activation email to %s", to_email)

        else:
            messages.error(request, "Chyba při registraci. Zkontrolujte prosím zadané údaje.")
    else:
        form = UserRegistrationForm()

    return render(request, "registration/create_account.html", {"form": form})


def activate_account(request, uidb64, token):
    """Handle account activation via email link.

    - Decodes UID and validates token.
    - Activates the user if valid, then logs them in.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None:
        messages.error(request, "Aktivace účtu selhala. Odkaz může být neplatný nebo vypršel.")
        logger.warning("Account activation failed - invalid UID: %s", uidb64)
        return redirect("sign_up")  # Redirect to registration or an error page
    if not account_activation_token.check_token(user, token):
        messages.error(request, "Aktivace účtu selhala. Odkaz může být neplatný nebo vypršel.")
        logger.warning("Failed to activate user account - invalid token for user: %s (ID: %s)", user.username or "(Anonymous)", user.pk)
        return redirect("sign_up")  # Redirect to registration or an error page

    user.is_active = True
    user.save()
    messages.success(request, "Účet byl úspěšně aktivován! Nyní se můžete přihlásit.")
    logger.info("User account activated: %s (ID: %s)", user.username or "(Anonymous)", user.pk)
    return redirect("login")


@login_required
def download_songbook_tex(request: HttpRequest):
    """Return a LaTeX source file containing all songs in the database. Only accessible to users in the "Song Admins" group."""
    if not request.user.groups.filter(name="Song Admins").exists():
        messages.error(request, "Nemáte oprávnění stáhnout zdrojový kód zpěvníku.")
        logger.warning("Unauthorized attempt to download songbook LaTeX by user: %s (ID: %s)", request.user.username or "(Anonymous)", request.user.pk)
        return redirect(reverse("tomikuvzpevnik:index"))  # Redirect if not authorized

    songs = Song.objects.all()
    tex_content = [base_to_tex(song.lyrics, song.title, song.artist, song.capo) for song in songs]
    response = HttpResponse("".join(tex_content), content_type="text/plain")
    response["Content-Disposition"] = "attachment; filename=songbook.tex"
    return response
