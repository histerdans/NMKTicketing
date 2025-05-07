from crispy_forms.helper import FormHelper
from crispy_forms.layout import Row, Layout, Column, Field
from django import forms
from django.utils import timezone

from .models import Ticket, Signature, PreventiveMaintenance, AntivirusKey, AntivirusUsage


class TicketForm(forms.ModelForm):
    ISSUE_CHOICES = [
        ('', 'Select Issue..'),
        ('Network', 'Network Issue'),
        ('Hardware', 'Hardware Issue'),
        ('Software', 'Software Issue'),
        ('Office Assistance', 'Office Assistance'),
        ('Physical Conference/Meetings', 'Physical Conference/Meetings'),
        ('Virtual Conference/Meetings', 'Virtual Conference/Meetings'),
    ]

    title = forms.ChoiceField(required=True, choices=ISSUE_CHOICES)

    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'priority', 'category','due_date','technician', 'attachment'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ticket title'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the issue'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'technician': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }





class SignatureForm(forms.ModelForm):
    class Meta:
        model = Signature
        fields = ['user_signature', 'technician_signature', 'remarks', 'follow_up']

    remarks = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super(SignatureForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column(Field('remarks'), css_class='col-8'),
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        user_signature = cleaned_data.get('user_signature')
        technician_signature = cleaned_data.get('technician_signature')

        if not user_signature:
            self.add_error('user_signature', 'User signature cannot be empty.')
        if not technician_signature:
            self.add_error('technician_signature', 'Technician signature cannot be empty.')

class PreventiveMaintenanceForm(forms.ModelForm):
    antivirus_key = forms.ModelChoiceField(queryset=AntivirusKey.objects.all())

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user  # Store the user in the form instance

        # Exclude antivirus keys that have already been used by this user
        if user:
            used_keys = AntivirusUsage.objects.filter(user=user).values_list('antivirus_key', flat=True)
            self.fields['antivirus_key'].queryset = AntivirusKey.objects.exclude(id__in=used_keys)

    class Meta:
        model = PreventiveMaintenance
        fields = ['antivirus_key', 'department', 'machine_type', 'computer_name', 'ipaddress',
                  'cpu_serial_no', 'monitor_serial_no', 'keyboard_serial_no', 'mouse_serial_no',
                  'printer_serial_no', 'ram', 'hdd', 'processor', 'follow_up', 'supervisor', 'remarks']
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'machine_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Machine Type'}),
            'computer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Computer Name'}),
            'ipaddress': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'IP Address'}),
            'cpu_serial_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CPU Serial Number'}),
            'monitor_serial_no': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Monitor Serial Number'}),
            'keyboard_serial_no': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Keyboard Serial Number'}),
            'mouse_serial_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mouse Serial Number'}),
            'printer_serial_no': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Printer Serial Number'}),
            'antivirus': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Antivirus'}),
            'antivirus_key': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Antivirus Serial'}),
            'ram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RAM'}),
            'hdd': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'HDD'}),
            'processor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Processor'}),
            'follow_up': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'supervisor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supervisor'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Remarks', 'rows': 3}),

        }

    def clean_antivirus_key(self):
        antivirus_key = self.cleaned_data.get('antivirus_key')

        # Ensure that user is set
        if self.user is None:
            raise forms.ValidationError('User not found.')

        # Check if the antivirus key is available for this user
        if not antivirus_key.available_for_user(self.user):
            raise forms.ValidationError('You have already used this antivirus key or it is unavailable.')

        return antivirus_key

    def save(self, commit=True):
        # Override save to assign the ticket to the preventive maintenance instance
        instance = super().save(commit=False)

        # Set the user to the logged-in user
        instance.user = self.user

        if commit:
            instance.save()  # Save the preventive maintenance record

            # After saving the preventive instance, create a related ticket
            ticket = Ticket(
                title='Preventive Maintenance',
                description='Request for preventive maintenance',
                user=self.user
            )
            ticket.save()

            # Assign the ticket to the preventive maintenance record
            instance.ticket = ticket
            instance.card_id = ticket.ticket_number  # Assign ticket number to the card_id field

            instance.save()  # Save the instance again with the ticket info

        return instance

class AddAntivirusKeyForm(forms.ModelForm):
    class Meta:
        model = AntivirusKey
        fields = ['key', 'suffix']  # Include the 'suffix' field

    def clean_key(self):
        key = self.cleaned_data['key']
        # Additional validation for the key format can go here
        return key



