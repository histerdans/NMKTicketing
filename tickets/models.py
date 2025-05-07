from django.core.exceptions import ValidationError
from django.db import models
import secrets
import string
from accounts.models import User


STATUS_CHOICES = [
    ('Open', 'Open'),
    ('In Progress', 'In Progress'),
    ('Resolved', 'Resolved'),
    ('Closed', 'Closed'),
]

PRIORITY_CHOICES = [
    ('Low', 'Low'),
    ('Medium', 'Medium'),
    ('High', 'High'),
]

CATEGORY_CHOICES = [
    ('Hardware', 'Hardware'),
    ('Software', 'Software'),
    ('Network', 'Network'),
    ('Other', 'Other'),
]

class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    title = models.CharField(max_length=200)
    ticket_number = models.CharField(max_length=20, unique=True, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='Open')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    resolution_date = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    follow_up = models.BooleanField(default=False)
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='assigned_tickets', null=True, blank=True)
    doneby = models.CharField(max_length=100)
    attachment = models.FileField(upload_to='media/attachments/', null=True, blank=True)


    def __str__(self):
        return f"{self.ticket_number} - {self.title} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    def save(self, *args, **kwargs):
        # Generate a random ticket number if it does not exist
        if not self.ticket_number:
            random_string = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(6))
            self.ticket_number = f"nmkict-{random_string}"

        super().save(*args, **kwargs)


class Signature(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='signature')
    user_signature = models.TextField(blank=False, null=True)
    technician_signature = models.TextField(blank=False, null=True)
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='signed_tickets')  # ICT staff who signed the ticket
    remarks = models.TextField(null=True, blank=True)
    signed_at = models.DateTimeField(auto_now_add=True)
    follow_up = models.BooleanField(default=False)

    def __str__(self):
        return f"Signatures for Ticket: {self.ticket.title}"

    def is_closed(self):
        return self.user_signature and self.technician_signature and self.remarks and self.technician and self.signed_at


class AntivirusKey(models.Model):
    key = models.CharField(max_length=255)
    max_uses_per_user = models.IntegerField(default=1)
    suffix = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.suffix}"

    def available_for_user(self, user):
        """
        Checks if the antivirus key is available for the specified user
        based on the max uses allowed.
        """
        used_count = AntivirusUsage.objects.filter(user=user, antivirus_key=self).count()
        return used_count < self.max_uses_per_user



class AntivirusUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    antivirus_key = models.ForeignKey(AntivirusKey, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'antivirus_key')

class PreventiveMaintenance(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Activated', 'Activated'),
    ]
    card_id = models.CharField(max_length=20, blank=True, null=True)  # Storing the ticket number
    ticket = models.ForeignKey('Ticket', on_delete=models.SET_NULL, null=True)  # Link to the Ticket model
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    machine_type = models.CharField(max_length=100)
    computer_name = models.CharField(max_length=100)
    ipaddress = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    cpu_serial_no = models.CharField(max_length=100)
    monitor_serial_no = models.CharField(max_length=100)
    keyboard_serial_no = models.CharField(max_length=100)
    mouse_serial_no = models.CharField(max_length=100)
    printer_serial_no = models.CharField(max_length=100, blank=True, null=True)
    ram = models.CharField(max_length=50)
    hdd = models.CharField(max_length=50)
    processor = models.CharField(max_length=50)
    antivirus_key = models.ForeignKey('AntivirusKey', on_delete=models.SET_NULL, null=True)
    follow_up = models.BooleanField(default=False)
    supervisor = models.CharField(max_length=100)
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Preventive Maintenance for {self.user} ({self.card_id})"

    def save(self, *args, **kwargs):
        # Ensure card_id matches ticket_number if the ticket is available
        if self.ticket:  # Check if ticket is not None
            self.card_id = self.ticket.ticket_number
        else:
            self.card_id = None  # Handle the case where ticket is None

        super().save(*args, **kwargs)
import logging
from django.db import models

# Get an instance of a logger
logger = logging.getLogger('tickets')  # 'myapp' is the name of the logger we defined in settings

class MyModel(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def save(self, *args, **kwargs):
        if self.pk:
            logger.info(f'Updated: {self.__class__.__name__} with ID {self.pk}')
        else:
            logger.info(f'Created: {self.__class__.__name__}')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        logger.info(f'Deleted: {self.__class__.__name__} with ID {self.pk}')
        super().delete(*args, **kwargs)