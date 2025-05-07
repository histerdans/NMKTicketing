from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from phonenumbers import NumberParseException, parse, is_possible_number, is_valid_number


class UserManager(BaseUserManager):
    def create_user(self,employee_name, department, username, email, password=None):
        """
        Creates and saves a User with the given email, username, and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            username=username,
            employee_name=employee_name,
            department=department,
            email=self.normalize_email(email),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, employee_name, username, email, password, department):
        """
        Creates and saves a superuser with the given email, username, and password.
        """
        user = self.create_user(employee_name, department, username, email, password)
        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)
        return user


def validate_phone_number(value):
    try:
        phone_number = parse(value, None)
        if not is_possible_number(phone_number):
            raise ValidationError(_('The phone number is not possible.'))
        if not is_valid_number(phone_number):
            raise ValidationError(_('The phone number is not valid.'))
    except NumberParseException as e:
        raise ValidationError(str(e))


class User(AbstractBaseUser):
    username = models.CharField(max_length=100, unique=True)
    department = models.CharField(max_length=200)
    email = models.EmailField(max_length=255, unique=True)
    employee_name = models.CharField(max_length=100)
    birth_date = models.DateTimeField(blank=False, default=timezone.now)
    phone_number = PhoneNumberField(region="GB", verbose_name="Mobile Number", help_text="Enter your phone number with "
                                                                                         "country code.")

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    def __str__(self):
        return f"{self.employee_name} - {self.department}"

    def has_perm(self, perm, obj=None):
        """
        Return True if the user has a permission.
        """
        return self.is_admin

    def has_module_perms(self, app_label):
        """
        Return True if the user has any permissions in the given app label.
        """
        return True

    USERNAME_FIELD = 'username'  # username
    # USERNAME_FIELD and password are required by default
    REQUIRED_FIELDS = ['email', 'employee_name', 'department']  # #python manage.py createsuperuser

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def get_absolute_url(self):
        return '/users/%s/'

    def get_username(self):
        if self.username:
            return self.username
        return self.email

    def get_short_name(self):
        return self.email


class ContactQuerySet(models.query.QuerySet):

    def search(self, query):
        lookups = (Q(title__icontains=query) |
                   Q(date__icontains=query)
                   )
        return self.filter(lookups).distinct()


class FeedbackManager(models.Manager):
    def get_queryset(self):
        return ContactQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset()

    def get_by_id(self, pk):
        qs = self.get_queryset().filter(id=pk)
        if qs.count() == 1:
            return qs.first()
        return None

    def search(self, query):
        return self.get_queryset().search(query)


class Feedback(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    f_name = models.CharField(max_length=255, )
    f_message = models.TextField(max_length=2255, )
    f_email = models.EmailField(max_length=255, unique=False)
    f_reply = models.TextField(max_length=2255, unique=False, default='Hi Friend, Thank you For you feedback!!!')

    objects = FeedbackManager()

    class Meta:
        verbose_name_plural = 'Feedbacks'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"{self.f_name} - {self.f_email}"
