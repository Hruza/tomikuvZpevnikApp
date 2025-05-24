from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.sites.shortcuts import get_current_site
from django.views import generic
from django.db.models.functions import Collate
from django.http import HttpRequest, JsonResponse
from django.urls import reverse
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string

from random import choice, choices
from tomikuvzpevnik.forms import SongEditForm
from tomikuvzpevnik.song_utils.conversions import ultimate_to_base
from django.db.models import BooleanField, Subquery, OuterRef
from .models import Song, SongData
from .forms import AddSongForm, UserRegistrationForm
from django.contrib import messages
from .tokens import account_activation_token
from django.contrib import messages


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

    def get_object(self, queryset=None):
        self.pk_url_kwarg
        self.song = super().get_object(queryset)
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
        if rng_mode not in {"0", "1", "2"}:
            rng_mode = "0"
        context["rng_mode"] = rng_mode
        return context


def get_random_song(request: HttpRequest):
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
def add_song(request: HttpRequest):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = AddSongForm(request.POST)

        if form.is_valid():
            # check whether it's valid:
            if form.cleaned_data["song_url"].strip() == "":
                request.session["unsaved_song_data"] = {}
                return redirect(reverse("tomikuvzpevnik:song_edit", args=(0,)))
            song_data = ultimate_to_base(form.cleaned_data["song_url"])
            if song_data is not None:
                request.session["unsaved_song_data"] = song_data
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
        if "favorite" not in request.POST.keys():
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
def edit_song(request: HttpRequest, pk: int):
    if pk == 0:
        song_data = request.session.get("unsaved_song_data", None)
        if song_data is None:
            return redirect(reverse("tomikuvzpevnik:index"))
        song = Song(**song_data, owner=request.user)
    else:
        song = get_object_or_404(Song, id=pk)

    if not song.isEditable(request.user):
        return redirect(
            reverse("tomikuvzpevnik:song_page", args=(pk,))
        )  # Redirect if not authorized

    if request.method == "POST":
        form = SongEditForm(request.POST, instance=song)
        if form.is_valid():
            new_song = form.save()
            return redirect(reverse("tomikuvzpevnik:song_page", args=(new_song.pk,)))
    else:
        form = SongEditForm(instance=song)

    return render(request, "tomikuvzpevnik/editSong.html", {"form": form, "song": song})


@login_required
def delete_song(request: HttpRequest, pk: int):
    song = get_object_or_404(Song, id=pk)

    if (
        song.owner != request.user
        and not request.user.groups.filter(name="Song Admins").exists()
    ):
        messages.error(request, "Nemáte oprávnění smazat tuto píseň.")
        return redirect(
            reverse("tomikuvzpevnik:song_edit", args=(pk,))
        )  # Redirect if not authorized

    if request.method == "POST":
        song.delete()
        messages.success(request, "Píseň byla úspěšně smazána.")
        return redirect(reverse("tomikuvzpevnik:index"))


def register(request: HttpRequest):
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect("login")

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Save the user with is_active=False initially
            user = form.save(commit=False)
            user.is_active = False # Account is inactive until email is verified
            user.save()

            # --- Email Verification Logic ---
            current_site = get_current_site(request)
            mail_subject = 'Tomíkův Zpěvník: aktivace účtu'
            message = render_to_string("registration/account_activation_email.html", {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            try:
                email.send()
                messages.success(request, "Please confirm your email address to complete the registration. An activation link has been sent to your email.")
                return redirect('login') # Redirect to login page after successful registration
            except Exception as e:
                # If email sending fails, delete the user or mark for review
                user.delete() # Or set a flag for admin review
                messages.error(request, f"There was an error sending the activation email. Please try again later. Error: {e}")
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send activation email to {to_email}: {e}")

        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = UserRegistrationForm()


    return render(request, "registration/create_account.html", {"form": form})

def activate_account(request, uidb64, token):
    """
    Handles account activation via email link.
    - Decodes UID and validates token.
    - Activates the user if valid, then logs them in.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user) # Log the user in immediately after activation
        messages.success(request, "Your account has been activated successfully! You are now logged in.")
        return redirect("login")
    else:
        # Security Priority: Generic error message for invalid/expired links.
        messages.error(request, "The activation link is invalid or has expired. Please try registering again or contact support.")
        return redirect('myapp:register') # Redirect to registration or an error page
