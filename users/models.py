from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager for CustomUser that uses phone as the login identifier,
    while keeping Django's required `username` field in sync automatically.
    """

    def _create_user(self, phone, password, **extra_fields):
        if not phone:
            raise ValueError('Поле "Номер телефона" обязательно для заполнения')

        # Keep username in sync with phone so AbstractUser's unique
        # username field never blocks user creation (see forms.py).
        extra_fields.setdefault('username', phone)

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True')

        return self._create_user(phone, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom user model using phone number as the primary identifier."""
    phone = models.CharField(
        'Номер телефона',
        max_length=20,
        unique=True,
        help_text='Формат: +7 (XXX) XXX-XX-XX'
    )
    email = models.EmailField(
        'Email',
        blank=True,
        null=True,
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.phone})'