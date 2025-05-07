from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from phonenumber_field.formfields import PhoneNumberField

from .models import User


class RegisterForm(UserCreationForm):
    employee_name = forms.CharField(max_length=255, required=False)
    department = forms.CharField(max_length=100, required=True)
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    username = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone_number = PhoneNumberField(region="GB", widget=forms.TextInput(attrs={'placeholder': 'e.g. +12345678901'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput, required=True)

    class Meta:
        model = User
        fields = ('employee_name','department', 'birth_date', 'username', 'email', 'phone_number', 'password1', 'password2')

    widgets = {
        'birth_date': forms.DateTimeInput(attrs={'type': 'date'}),
    }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords don\'t match.')
        return password2

    def clean_email(self):
        email = self.cleaned_data['email']
        UserModel = get_user_model()
        if UserModel.objects.filter(email=email).exists():
            raise ValidationError('Email already exists.')
        return email


class UpdateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('employee_name','department', 'birth_date', 'username', 'email', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(UpdateForm, self).__init__(*args, **kwargs)
        self.fields['employee_name'].widget.attrs.update(
            {'type': 'text', 'class': 'span12', 'id': 'employee_name', 'name': 'employee_name', })
        self.fields['email'].widget.attrs.update(
            {'type': 'email', 'class': 'span12', 'id': 'email', 'name': 'email', 'placeholder': 'Email'})
        self.fields['username'].widget.attrs.update(
            {'type': 'text', 'class': 'span12', 'id': 'username', 'name': 'username', 'placeholder': 'Username'})
        self.fields['phone_number'].widget.attrs.update(
            {'type': 'tel'})
        self.fields['birth_date'].widget.attrs.update(
            {'type': 'text', 'class': 'span12', 'id': 'birth_date', 'name': 'birth_date'})
        self.fields['password1'].widget.attrs.update(
            {'type': 'password', 'class': 'span12', 'id': 'password1', 'name': 'password1', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update(
            {'type': 'password', 'class': 'span12', 'password2': 'password2', 'name': 'Password2',
             'placeholder': 'Confirm Password'})
