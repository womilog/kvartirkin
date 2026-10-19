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
        unique=True,
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.phone})'


class PasswordResetToken(models.Model):
    """Token for password reset via email."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
    )
    token = models.CharField('Token', max_length=255, unique=True)
    created_at = models.DateTimeField('Created at', auto_now_add=True)
    expires_at = models.DateTimeField('Expires at')
    used = models.BooleanField('Used', default=False)

    class Meta:
        verbose_name = 'Токен сброса пароля'
        verbose_name_plural = 'Токены сброса пароля'

    def __str__(self):
        status = 'used' if self.used else 'active'
        return f'{self.user.email} — {status}'

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() >= self.expires_at

    def save(self, *args, **kwargs):
        if not self.expires_at:
            from django.utils.timezone import now, timedelta
            self.expires_at = now() + timedelta(hours=1)
        super().save(*args, **kwargs)