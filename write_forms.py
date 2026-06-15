content = """\
import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

CustomUser = get_user_model()


class RegistrationForm(forms.ModelForm):
    \"\"\"Form for user registration with phone number.\"\"\"
    password = forms.CharField(
        label='\u041f\u0430\u0440\u043e\u043b\u044c',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': '\u041c\u0438\u043d\u0438\u043c\u0443\u043c 8 \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432',
        }),
        min_length=8,
    )
    password_confirm = forms.CharField(
        label='\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u0435 \u043f\u0430\u0440\u043e\u043b\u044f',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': '\u041f\u043e\u0432\u0442\u043e\u0440\u0438\u0442\u0435 \u043f\u0430\u0440\u043e\u043b\u044c',
        }),
    )
    agree_terms = forms.BooleanField(
        label='\u042f \u0441\u043e\u0433\u043b\u0430\u0441\u0435\u043d \u0441 \u0443\u0441\u043b\u043e\u0432\u0438\u044f\u043c\u0438 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u044f \u0438 \u043f\u043e\u043b\u0438\u0442\u0438\u043a\u043e\u0439 \u043a\u043e\u043d\u0444\u0438\u0434\u0435\u043d\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u0438',
        required=True,
        error_messages={'required': '\u041d\u0435\u043e\u0431\u0445\u043e\u0434\u0438\u043c\u043e \u043f\u0440\u0438\u043d\u044f\u0442\u044c \u0443\u0441\u043b\u043e\u0432\u0438\u044f'},
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
                'placeholder': '\u0418\u043c\u044f',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
                'placeholder': '\u0424\u0430\u043c\u0438\u043b\u0438\u044f',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
                'placeholder': '+7 (___) ___-__-__',
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        # Strip all non-digit characters
        digits = re.sub(r'\\D', '', phone)
        if not digits.startswith('7') and not digits.startswith('8'):
            raise forms.ValidationError('\u041d\u043e\u043c\u0435\u0440 \u0434\u043e\u043b\u0436\u0435\u043d \u043d\u0430\u0447\u0438\u043d\u0430\u0442\u044c\u0441\u044f \u0441 +7 \u0438\u043b\u0438 8')
        if len(digits) != 11:
            raise forms.ValidationError('\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u044b\u0439 \u043d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430 (11 \u0446\u0438\u0444\u0440)')
        # Normalize to +7XXXXXXXXXX format
        normalized = '+7' + digits[1:]
        if CustomUser.objects.filter(phone=normalized).exists():
            raise forms.ValidationError('\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0441 \u0442\u0430\u043a\u0438\u043c \u043d\u043e\u043c\u0435\u0440\u043e\u043c \u0443\u0436\u0435 \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d')
        return normalized

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('\u041f\u0430\u0440\u043e\u043b\u0438 \u043d\u0435 \u0441\u043e\u0432\u043f\u0430\u0434\u0430\u044e\u0442')
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


class LoginForm(AuthenticationForm):
    \"\"\"Form for user login with phone number.\"\"\"
    username = forms.CharField(
        label='\u0422\u0435\u043b\u0435\u0444\u043e\u043d',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': '+7 (___) ___-__-__',
        }),
    )
    password = forms.CharField(
        label='\u041f\u0430\u0440\u043e\u043b\u044c',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022',
        }),
    )

    def clean_username(self):
        phone = self.cleaned_data.get('username', '')
        # Strip all non-digit characters
        digits = re.sub(r'\\D', '', phone)
        if len(digits) == 11:
            # Normalize to +7XXXXXXXXXX format
            return '+7' + digits[1:]
        return phone
"""

with open('users/forms.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done. Verifying syntax...')
import py_compile
try:
    py_compile.compile('users/forms.py', doraise=True)
    print('Syntax OK')
except py_compile.PyCompileError as e:
    print(f'Syntax ERROR: {e}')