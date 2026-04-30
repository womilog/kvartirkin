from django.contrib.auth.models import AbstractUser
from django.db import models


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

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.phone})'