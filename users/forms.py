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
        fields = ['first_name', 'last_name', 'phone']
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
        }

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
        if commit:
            user.save()
        return user


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
