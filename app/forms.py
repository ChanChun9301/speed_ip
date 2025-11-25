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
        fields = ('username', 'first_name', 'last_name')

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
]

class GoogleDorkingForm(forms.Form):
    text_input = forms.CharField(label='Поисковый запрос', max_length=255)
    dork_command = forms.ChoiceField(label='Команда Dorking', choices=DORK_CHOICES, required=False)

# ============================================================
# 🌐 НОВЫЕ ФОРМЫ (старые НЕ изменены)
# ============================================================

# ✔ Форма проверки ping
class PingCheckForm(forms.Form):
    ip_address = forms.GenericIPAddressField(
        label="IP адрес для ping",
        help_text="Введите IPv4 или IPv6"
    )

# ✔ Форма поиска ExploitExample по категории
class ExploitFilterForm(forms.Form):
    category = forms.CharField(
        required=False,
        label="Категория Exploit",
        widget=forms.TextInput(attrs={'placeholder': 'Например: wordpress, apache, rce'})
    )

# ✔ Форма для фильтрации SpeedTestResult
class SpeedTestFilterForm(forms.Form):
    ip = forms.CharField(
        required=False,
        label="IP фильтр",
        widget=forms.TextInput(attrs={'placeholder': 'Введите IP или часть IP'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Дата от"
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Дата до"
    )

# ✔ Форма добавления новой команды
class CommandCreateForm(forms.ModelForm):
    class Meta:
        model = Commands
        fields = ["command", "description"]

# ✔ Форма добавления нового примера Exploit
class ExploitCreateForm(forms.ModelForm):
    class Meta:
        model = ExploitExample
        fields = ["category", "description", "exploit_filename", "url"]

class Base64Form(forms.Form):
    text = forms.CharField(widget=forms.Textarea, label="Введите текст / Base64")

class UrlForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, label="Введите текст / URL encoded")

class HashForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, label="Введите текст")

class TextToolForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, required=False)
    mode = forms.ChoiceField(choices=[
        ('uuid', 'Генерация UUID'),
        ('random', 'Случайная строка'),
        ('stats', 'Статистика текста'),
        ('upper', 'В верхний регистр'),
        ('lower', 'В нижний регистр'),
        ('uniq', 'Удалить дубликаты'),
    ])
