from django import forms

class ContactUSForm(forms.Form):
    name = forms.CharField(max_length=255, required=True, error_messages={'required': 'Name is required.'})
    email = forms.EmailField(required=True, error_messages={'required': 'Email is required.'})
    phone = forms.CharField(max_length=10, required=False)
    communication_method  = forms.ChoiceField(choices=[('email', 'Email'), ('phone', 'Phone')], required=True, error_messages={'required': 'Phone Number is required.'})
    message = forms.CharField(widget=forms.Textarea, required=True,error_messages={'required': 'Write Something Here..'})
    

