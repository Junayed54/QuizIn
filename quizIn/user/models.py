from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, msisdn, password=None, username=None, **extra_fields):
        """
        Create and return a regular user with a mobile number (msisdn) and password.
        """
        if not msisdn:
            raise ValueError('The MSISDN (Mobile number) must be set')
        user = self.model(msisdn=msisdn, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, msisdn, username=None, password=None, **extra_fields):
        """
        Create and return a superuser with a mobile number (msisdn) and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(msisdn, password, username=username, **extra_fields)

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    msisdn = models.CharField(max_length=15, unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)  # We are removing the username field
    email = models.EmailField(unique=True, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    USERNAME_FIELD = 'msisdn'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()  # Using the custom manager

    def __str__(self):
        return self.msisdn
