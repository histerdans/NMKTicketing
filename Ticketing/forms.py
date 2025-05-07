from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field
from django import forms

from accounts.models import Feedback


class ContactForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ('f_name', 'f_email', 'f_message')

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column(Field('f_name', css_class='col-md-4'), css_class='form-group', ),
                Column(Field('f_email', css_class='col-md-4'), css_class='form-group'),
                Column(Field('f_message', css_class='col-md-4'), css_class='form-group'),
            ),
        )
