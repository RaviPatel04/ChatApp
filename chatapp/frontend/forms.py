from django import forms

class ContactUSForm(forms.Form):
    name = forms.CharField(max_length=255, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=10, required=False)
    communication_method  = forms.ChoiceField(choices=[('email', 'Email'), ('phone', 'Phone')], required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)
    

