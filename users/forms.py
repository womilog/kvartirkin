import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

CustomUser = get_user_model()


class RegistrationForm(forms.ModelForm):
    """Form for user registration with phone number."""
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': 'Минимум 8 символов',
        }),
        min_length=8,
    )
    password_confirm = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': 'Повторите пароль',
        }),
    )
    agree_terms = forms.BooleanField(
        label='Я согласен с условиями использования и политикой конфиденциальности',
        required=True,
        error_messages={'required': 'Необходимо принять условия'},
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
                'placeholder': 'Имя',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
                'placeholder': 'Фамилия',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
                'placeholder': '+7 (___) ___-__-__',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
                'placeholder': 'you@example.com',
            }),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password', '')

        if len(password) > 128:
            raise forms.ValidationError('Пароль не должен превышать 128 символов')

        # Check for digits
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну цифру')

        # Check for Latin letters
        if not re.search(r'[A-Za-z]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну латинскую букву')

        # Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=/\[\]\\~`]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы один специальный символ')

        # Check for Cyrillic letters (not allowed)
        if re.search(r'[А-Яа-яЁё]', password):
            raise forms.ValidationError('Пароль не должен содержать буквы кириллицы')

        # Check for common/weak passwords
        weak_passwords = {
            '12345678', '123456789', '1234567890',
            'qwerty123', 'qwerty1234', 'password123',
            'admin123', 'root123', 'test123',
            '11111111', '00000000',
            'password', 'qwerty', 'letmein',
        }
        if password.lower() in weak_passwords:
            raise forms.ValidationError('Пароль слишком простой, выберите более сложный')

        return password

        

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email обязателен для заполнения')
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        # Strip all non-digit characters
        digits = re.sub(r'\D', '', phone)
        if not digits.startswith('7') and not digits.startswith('8'):
            raise forms.ValidationError('Номер должен начинаться с +7 или 8')
        if len(digits) != 11:
            raise forms.ValidationError('Введите корректный номер телефона (11 цифр)')
        # Normalize to +7XXXXXXXXXX format
        normalized = '+7' + digits[1:]
        if CustomUser.objects.filter(phone=normalized).exists():
            raise forms.ValidationError('Пользователь с таким номером уже зарегистрирован')
        return normalized

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        # AbstractUser still has a unique 'username' field even though
        # USERNAME_FIELD = 'phone'. Set it to the phone number to avoid
        # UNIQUE constraint failures on repeated registrations.
        user.username = self.cleaned_data['phone']
        if commit:
            user.save()
        return user


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile information."""
    password = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': 'Оставьте пустым, если не меняете пароль',
        }),
        required=False,
    )
    password_confirm = forms.CharField(
        label='Подтверждение нового пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': 'Повторите новый пароль',
        }),
        required=False,
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'email']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'phone': 'Телефон',
            'email': 'Email',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
                'placeholder': 'Имя',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
                'placeholder': 'Фамилия',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
                'placeholder': '+7 (___) ___-__-__',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
                'placeholder': 'you@example.com',
            }),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password', '')

        # If password is empty, skip validation (user not changing password)
        if not password:
            return password

        if len(password) < 8:
            raise forms.ValidationError('Пароль не должен быть меньше 8 символов')
        
        if len(password) > 128:
            raise forms.ValidationError('Пароль не должен превышать 128 символов')

        if not re.search(r'[0-9]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну цифру')

        if not re.search(r'[A-Za-z]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну латинскую букву')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=/\[\]\\~`]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы один специальный символ')

        if re.search(r'[А-Яа-яЁё]', password):
            raise forms.ValidationError('Пароль не должен содержать буквы кириллицы')

        weak_passwords = {
            '12345678', '123456789', '1234567890',
            'qwerty123', 'qwerty1234', 'password123',
            'admin123', 'root123', 'test123',
            '11111111', '00000000',
            'password', 'qwerty', 'letmein',
        }
        if password.lower() in weak_passwords:
            raise forms.ValidationError('Пароль слишком простой, выберите более сложный')

        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Новые пароли не совпадают')
        return cleaned_data

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        digits = re.sub(r'\D', '', phone)
        if not digits.startswith('7') and not digits.startswith('8'):
            raise forms.ValidationError('Номер должен начинаться с +7 или 8')
        if len(digits) != 11:
            raise forms.ValidationError('Введите корректный номер телефона (11 цифр)')
        normalized = '+7' + digits[1:]
        # Ensure phone is not used by another user
        qs = CustomUser.objects.filter(phone=normalized).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Пользователь с таким номером уже зарегистрирован')
        return normalized

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email
        qs = CustomUser.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Этот email уже используется другим аккаунтом')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['phone']
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class CustomPasswordChangeForm(forms.Form):
    """Form for changing password with custom validation."""
    old_password = forms.CharField(
        label='Текущий пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': '••••••••',
        }),
        required=True,
    )
    new_password = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': 'Минимум 8 символов',
        }),
        required=True,
    )
    new_password_confirm = forms.CharField(
        label='Подтверждение нового пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': 'Повторите новый пароль',
        }),
        required=True,
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password', '')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Неверный текущий пароль')
        return old_password

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password', '')

        if len(password) < 8:
            raise forms.ValidationError('Пароль не должен быть меньше 8 символов')

        if len(password) > 128:
            raise forms.ValidationError('Пароль не должен превышать 128 символов')

        if not re.search(r'[0-9]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну цифру')

        if not re.search(r'[A-Za-z]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну латинскую букву')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=/\[\]\\~`]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы один специальный символ')

        if re.search(r'[А-Яа-яЁё]', password):
            raise forms.ValidationError('Пароль не должен содержать буквы кириллицы')

        weak_passwords = {
            '12345678', '123456789', '1234567890',
            'qwerty123', 'qwerty1234', 'password123',
            'admin123', 'root123', 'test123',
            '11111111', '00000000',
            'password', 'qwerty', 'letmein',
        }
        if password.lower() in weak_passwords:
            raise forms.ValidationError('Пароль слишком простой, выберите более сложный')

        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')
        if new_password and new_password_confirm and new_password != new_password_confirm:
            raise forms.ValidationError('Новые пароли не совпадают')
        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data['new_password'])
        self.user.save()
        return self.user


class LoginForm(AuthenticationForm):
    """Form for user login with phone number."""
    username = forms.CharField(
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': '+7 (___) ___-__-__',
        }),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': '••••••••',
        }),
    )

    def clean_username(self):
        phone = self.cleaned_data.get('username', '')
        # Strip all non-digit characters
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 11:
            # Normalize to +7XXXXXXXXXX format
            return '+7' + digits[1:]
        return phone


class RequestPasswordResetForm(forms.Form):
    """Form for requesting password reset via email."""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': 'you@example.com',
        }),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'Пользователь с таким email не найден. '
                'Убедитесь, что вы указали email при регистрации.'
            )
        return email


class ResetPasswordForm(forms.Form):
    """Form for resetting password with token."""
    new_password = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': 'Минимум 8 символов',
        }),
        min_length=8,
    )
    new_password_confirm = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': 'Повторите пароль',
        }),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password', '')

        if len(password) > 128:
            raise forms.ValidationError('Пароль не должен превышать 128 символов')

        if not re.search(r'[0-9]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну цифру')

        if not re.search(r'[A-Za-z]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну латинскую букву')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=/\[\]\\~`]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы один специальный символ')

        if re.search(r'[А-Яа-яЁё]', password):
            raise forms.ValidationError('Пароль не должен содержать буквы кириллицы')

        weak_passwords = {
            '12345678', '123456789', '1234567890',
            'qwerty123', 'qwerty1234', 'password123',
            'admin123', 'root123', 'test123',
            '11111111', '00000000',
            'password', 'qwerty', 'letmein',
        }
        if password.lower() in weak_passwords:
            raise forms.ValidationError('Пароль слишком простой, выберите более сложный')

        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')
        if new_password and new_password_confirm and new_password != new_password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        return cleaned_data
