from django import forms

class IPAddressForm(forms.Form):
    ip_addresses = forms.CharField(widget=forms.Textarea, help_text='Введите IP-адреса каждый на новой строке.')