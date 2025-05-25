from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.forms import ModelForm
from django import forms
from tomikuvzpevnik.models import Song
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from urllib.parse import urlparse
from django.contrib.auth.models import User


def validate_no_html(value):
    if "<" in value or ">" in value:
        raise ValidationError(f'Invalid characters in use: ">" or "<"', code="invalid")


def validate_url(value):
    if value.strip() == "":
        return
    else:
        parsed_url = urlparse(value)
        hostname = str(parsed_url.netloc)
        if not hostname.endswith("ultimate-guitar.com"):
            raise ValidationError("URL musí být ze stránky 'ultimate-guitar.com'")


class AddSongForm(forms.Form):
    song_url = forms.URLField(
        label="Zadej URL z ultimate-guitar.com",
        max_length=200,
        required=False,
        validators=[validate_url],
    )


class SongEditForm(ModelForm):
    title = forms.CharField(max_length=200, validators=[validate_no_html])
    artist = forms.CharField(max_length=200, validators=[validate_no_html])
    lyrics = forms.CharField(widget=forms.Textarea, validators=[validate_no_html])
    capo = forms.IntegerField(min_value=0, max_value=11, label="Capo", initial=0)

    class Meta:
        model = Song
        fields = ["title", "artist", "capo", "lyrics"]
        labels = {
            "title": "Název písničky",
            "artist": "Autor/Interpret",
            "capo": "Capo:",
            "lyrics": "Text písně:",
        }


class UserRegistrationForm(UserCreationForm):
    """
    A custom form for user registration.
    Extends Django's built-in UserCreationForm for convenience and security.
    It adds an 'email' field and ensures it's required and unique.
    """

    usable_password = None

    email = forms.EmailField(
        label="Email",
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "your.email@example.com"}),
        help_text="A valid email address is required.",
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ["email", "username", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = ""
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""
        self.fields["email"].help_text = ""

    def clean_email(self):
        """
        Custom clean method for the email field to ensure uniqueness.
        Security Priority: Prevent registration with an already existing email.
        """
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            # Security Priority: Generic error message to prevent email enumeration.
            # While this specifically mentions email, it's common practice for registration.
            raise forms.ValidationError("This email address is already registered.")
        return email

    def save(self, commit=True):
        """
        Overrides the save method to ensure the email is saved correctly
        and the user is created.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
