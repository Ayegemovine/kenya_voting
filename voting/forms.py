from django import forms
from django.contrib.auth.models import User
from .models import VoterProfile


KENYA_COUNTIES = [
    ('', '-- Select your County --'),
    ('Baringo', 'Baringo'),
    ('Bomet', 'Bomet'),
    ('Bungoma', 'Bungoma'),
    ('Busia', 'Busia'),
    ('Elgeyo-Marakwet', 'Elgeyo-Marakwet'),
    ('Embu', 'Embu'),
    ('Garissa', 'Garissa'),
    ('Homa Bay', 'Homa Bay'),
    ('Isiolo', 'Isiolo'),
    ('Kajiado', 'Kajiado'),
    ('Kakamega', 'Kakamega'),
    ('Kericho', 'Kericho'),
    ('Kiambu', 'Kiambu'),
    ('Kilifi', 'Kilifi'),
    ('Kirinyaga', 'Kirinyaga'),
    ('Kisii', 'Kisii'),
    ('Kisumu', 'Kisumu'),
    ('Kitui', 'Kitui'),
    ('Kwale', 'Kwale'),
    ('Laikipia', 'Laikipia'),
    ('Lamu', 'Lamu'),
    ('Machakos', 'Machakos'),
    ('Makueni', 'Makueni'),
    ('Mandera', 'Mandera'),
    ('Marsabit', 'Marsabit'),
    ('Meru', 'Meru'),
    ('Migori', 'Migori'),
    ('Mombasa', 'Mombasa'),
    ("Murang'a", "Murang'a"),
    ('Nairobi', 'Nairobi'),
    ('Nakuru', 'Nakuru'),
    ('Nandi', 'Nandi'),
    ('Narok', 'Narok'),
    ('Nyamira', 'Nyamira'),
    ('Nyandarua', 'Nyandarua'),
    ('Nyeri', 'Nyeri'),
    ('Samburu', 'Samburu'),
    ('Siaya', 'Siaya'),
    ('Taita-Taveta', 'Taita-Taveta'),
    ('Tana River', 'Tana River'),
    ('Tharaka-Nithi', 'Tharaka-Nithi'),
    ('Trans Nzoia', 'Trans Nzoia'),
    ('Turkana', 'Turkana'),
    ('Uasin Gishu', 'Uasin Gishu'),
    ('Vihiga', 'Vihiga'),
    ('Wajir', 'Wajir'),
    ('West Pokot', 'West Pokot'),
]


class RegisterForm(forms.Form):

    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. John Kamau',
            'class': 'form-input'
        })
    )

    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Choose a username',
            'class': 'form-input'
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'example@email.com',
            'class': 'form-input'
        })
    )

    national_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your National ID number',
            'class': 'form-input'
        })
    )

    county = forms.ChoiceField(
        choices=KENYA_COUNTIES,
        widget=forms.Select(attrs={'class': 'form-input'})
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create a strong password',
            'class': 'form-input'
        })
    )

    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Type your password again',
            'class': 'form-input'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match. Please try again.")

        username = cleaned_data.get('username')
        national_id = cleaned_data.get('national_id')

        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")

        if national_id and VoterProfile.objects.filter(national_id=national_id).exists():
            raise forms.ValidationError("This National ID is already registered.")

        return cleaned_data


class LoginForm(forms.Form):

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Your username',
            'class': 'form-input'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Your password',
            'class': 'form-input'
        })
    )