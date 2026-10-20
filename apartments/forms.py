import re
from datetime import date, timedelta
from django import forms
from .models import Reservation, Review


class BookingForm(forms.ModelForm):
    """Form for booking an apartment with date validation."""

    GUEST_CHOICES = [(i, f'{i} {"гость" if i == 1 else "гостя" if i < 5 else "гостей"}')
                     for i in range(1, 7)]

    CHECKIN_TIMES = [
        ('', 'После 14:00'),
        ('14:00', '14:00'),
        ('15:00', '15:00'),
        ('16:00', '16:00'),
        ('17:00', '17:00'),
        ('18:00', '18:00'),
    ]

    first_name = forms.CharField(
        label='Имя',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
        }),
    )
    last_name = forms.CharField(
        label='Фамилия',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
        }),
    )
    phone = forms.CharField(
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'placeholder': '+7 (___) ___-__-__',
        }),
    )
    check_in = forms.DateField(
        label='Дата заезда',
        widget=forms.DateInput(format='%d-%m-%Y',attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'lang': 'ru',
        }),
    )
    check_out = forms.DateField(
        label='Дата выезда',
        widget=forms.DateInput(format='%d-%m-%Y',attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
            'lang': 'ru',
        }),
    )
    guests = forms.ChoiceField(
        label='Количество гостей',
        choices=GUEST_CHOICES,
        initial=2,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
        }),
    )
    checkin_time = forms.ChoiceField(
        label='Время заезда',
        choices=CHECKIN_TIMES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all',
        }),
    )
    has_pet = forms.BooleanField(
        label='Еду с питомцем (+₽500/сутки)',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-sea-500 focus:ring-sea-500 w-5 h-5',
        }),
    )
    comment = forms.CharField(
        label='Комментарий',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all resize-none',
            'placeholder': 'Особые пожелания...',
        }),
    )
    agree_terms = forms.BooleanField(
        label='Я согласен с правилами проживания и политикой конфиденциальности',
        required=True,
        error_messages={'required': 'Необходимо принять условия'},
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-sea-500 focus:ring-sea-500 w-5 h-5 mt-0.5',
        }),
    )

    class Meta:
        model = Reservation
        fields = ['first_name', 'last_name', 'phone', 'check_in', 'check_out',
                  'guests', 'has_pet', 'comment']

    def __init__(self, *args, apartment=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.apartment = apartment

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 10:
            raise forms.ValidationError('Введите корректный номер телефона')
        return phone

    def clean_check_in(self):
        check_in = self.cleaned_data.get('check_in')
        if check_in and check_in < date.today():
            raise forms.ValidationError('Дата заезда не может быть в прошлом')
        return check_in

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')

        if check_in and check_out:
            if check_out <= check_in:
                raise forms.ValidationError('Дата выезда должна быть позже даты заезда')

            # Check for overlapping reservations
            overlapping = Reservation.objects.filter(
                apartment=self.apartment,
                status__in=['pending', 'confirmed'],
                check_in__lt=check_out,
                check_out__gt=check_in,
            )
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)

                if overlapping.exists():
                    raise forms.ValidationError(
                    'К сожалению, выбранные даты уже заняты. '
                    'Пожалуйста, выберите другие даты.'
                )

        return cleaned_data


class ReviewForm(forms.ModelForm):
    """Form for submitting a review on an apartment."""

    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    rating = forms.TypedChoiceField(
        label='Оценка',
        choices=RATING_CHOICES,
        coerce=int,
        widget=forms.RadioSelect(attrs={'class': 'rating-input'}),
        error_messages={'required': 'Пожалуйста, выберите оценку'},
    )
    text = forms.CharField(
        label='Текст отзыва',
        min_length=10,
        max_length=2000,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-3 rounded-lg bg-sand-50 border border-sand-200 focus:border-sea-500 focus:ring-2 focus:ring-sea-200 transition-all resize-none',
            'placeholder': 'Поделитесь впечатлениями о квартире...',
        }),
        error_messages={
            'required': 'Пожалуйста, напишите текст отзыва',
            'min_length': 'Отзыв должен быть не короче 10 символов',
            'max_length': 'Отзыв слишком длинный (максимум 2000 символов)',
        },
    )

    class Meta:
        model = Review
        fields = ['rating', 'text']

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None or rating < 1 or rating > 5:
            raise forms.ValidationError('Оценка должна быть от 1 до 5')
        return rating

    def clean_text(self):
        text = self.cleaned_data.get('text', '').strip()
        if not text:
            raise forms.ValidationError('Текст отзыва не может быть пустым')
        return text