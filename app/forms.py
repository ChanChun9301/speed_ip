from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import *

class SearchForm(forms.Form):
    text_input = forms.CharField(label='Search Term', max_length=255)
    dork_command = forms.CharField(label='Dork Command (Optional)', max_length=255, required=False)

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='',
        widget=forms.TextInput(
            attrs={'class': 'form__input', 'placeholder': 'Ulanyjy ady'}))
    password = forms.CharField(
        label='', 
        widget=forms.PasswordInput(
            attrs={'class': 'form__input', 'placeholder': 'Parol'}))




class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name') # Include the fields you want

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class IPAddressForm(forms.Form):
    ip_addresses = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        label='IP Salgylaryny Giriziň (her setirde bir):',
        help_text='Her IP salgysyny täze setirde giriziň.'
    )

DORK_CHOICES = [
    ('', 'Выберите команду (необязательно)'),
    ('site:', 'site:'),
    ('inurl:', 'inurl:'),
    ('intitle:', 'intitle:'),
    ('intext:', 'intext:'),
    ('filetype:', 'filetype:'),
    # Добавьте другие распространенные команды по мере необходимости
]

class GoogleDorkingForm(forms.Form):
    text_input = forms.CharField(label='Поисковый запрос', max_length=255)
    dork_command = forms.ChoiceField(label='Команда Dorking', choices=DORK_CHOICES, required=False)