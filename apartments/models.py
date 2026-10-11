from django.db import models
from django.urls import reverse


class VorkutaApartments(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(city=Apartment.City.VORKUTA)


class GelendzhikApartments(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(city=Apartment.City.GELENDZHIK)
    

class Apartment(models.Model):
    """Model for apartments available for daily rent."""
    class City(models.TextChoices):
        VORKUTA = ("Vorkuta", "Воркута")
        GELENDZHIK = ("Gelendzhik", "Геленджик")

    class Smoke(models.TextChoices):
        ZAPRET = ("zapret", "Запрещено")
        BALCONY = ("balcony", "На балконе")
        ENTRANCE = ("entrance", "В подъезде")
    
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('URL-слаг', unique=True)
    city = models.CharField("город", max_length=20, choices=City.choices, default=City.GELENDZHIK)
    address = models.CharField('Адрес', max_length=300)
    rooms = models.PositiveIntegerField('Количество комнат')
    area = models.DecimalField('Площадь (м²)', max_digits=6, decimal_places=1)
    price_per_day = models.DecimalField('Цена за сутки (₽)', max_digits=10, decimal_places=0)
    description = models.TextField('Описание')
    latitude = models.FloatField('Широта')
    longitude = models.FloatField('Долгота')
    max_guests = models.PositiveIntegerField('Максимум гостей', default=4)
    distance_to_sea = models.CharField('Расстояние до моря', max_length=100, blank=True)
    distance_to_center = models.CharField('Расстояние до центра Города', max_length=100, blank=True, default='')
    # main_image =
    has_wifi = models.BooleanField('Wi-Fi', default=False)
    has_smart_tv = models.BooleanField('Smart TV', default=False)
    has_washing_machine = models.BooleanField('Стиральная машина', default=False)
    has_ac = models.BooleanField('Кондиционер', default=False)
    pets_allowed = models.BooleanField('Можно с питомцем', default=False)
    free_private_park = models.BooleanField("Бесплатная частная парковка", default=False)
    near_pool = models.BooleanField("Открытый бассейн рядом", default=False)
    avaible_smoke = models.CharField("Разрешено курить", max_length=20, choices=Smoke.choices, default=Smoke.ZAPRET)

    is_active = models.BooleanField('Активна', default=True)
    bookings_enabled = models.BooleanField('Бронирование разрешено', default=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    objects = models.Manager()
    vorkuta = VorkutaApartments()
    gelendzhik = GelendzhikApartments()

    class Meta:
        verbose_name = 'Апартаменты'
        verbose_name_plural = 'Апартаменты'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('apartment_detail', kwargs={'slug': self.slug})

    @property
    def main_image(self):
        """Return the first image or None."""
        return self.images.first()

    def is_available_for_dates(self, check_in, check_out):
        """Check if apartment is available for given date range."""
        if not check_in or not check_out:
            return True
        
        overlapping = self.reservations.filter(
            status__in=['pending', 'confirmed'],
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exists()
        return not overlapping

    def get_current_availability(self):
        """Check if apartment is currently available (no overlapping reservations from today)."""
        from datetime import date
        today = date.today()
        overlapping = self.reservations.filter(
            status__in=['pending', 'confirmed'],
            check_in__lte=today,
            check_out__gt=today,
        ).exists()
        return not overlapping

    def can_be_booked(self):
        """Check if apartment can be booked (bookings are enabled and currently available)."""
        return self.bookings_enabled and self.is_active


class ApartmentImage(models.Model):
    """Images for an apartment."""
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Апартаменты'
    )
    image = models.ImageField('Фото', upload_to='apartments/')
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Фото апартаментов'
        verbose_name_plural = 'Фото апартаментов'
        ordering = ['order']

    def __str__(self):
        return f'Фото {self.order} — {self.apartment.name}'


class Reservation(models.Model):
    """Reservation for an apartment."""
        # The status field is intentionally kept: it drives the request workflow.
    #   pending   - request submitted, awaiting landlord decision (blocks dates)
    #   confirmed - landlord approved the request (blocks dates)
    #   rejected  - landlord declined the request (does NOT block dates)
    #   cancelled - guest cancelled the request (does NOT block dates)
    class Status(models.TextChoices):
        PENDING = ('pending', 'Ожидает подтверждения')
        CONFIRMED = ('confirmed', 'Подтверждено')
        REGECTED = ('rejected', 'Отклонено')
        CANCELLED = ('cancelled', 'Отменено')

    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name='Апартаменты'
    )
    user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name='Пользователь',
        null=True,
        blank=True,
    )

    # Contact info (for non-registered users too)
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    phone = models.CharField('Телефон', max_length=20)

    # Booking details
    check_in = models.DateField('Дата заезда')
    check_out = models.DateField('Дата выезда')
    guests = models.PositiveIntegerField('Количество гостей', default=1)
    has_pet = models.BooleanField('С питомцем', default=False)
    comment = models.TextField('Комментарий', blank=True)

    total_price = models.DecimalField('Итого (₽)', max_digits=10, decimal_places=0)
    status = models.CharField('Статус', max_length=20, choices=Status.choices, default='pending') # STATUS_CHOICES

    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.apartment.name} — {self.first_name} {self.last_name} ({self.check_in} — {self.check_out})'


class Review(models.Model):
    """Review/rating for an apartment."""
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Апартаменты'
    )
    user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Пользователь'
    )
    rating = models.PositiveIntegerField('Оценка', choices=[(i, i) for i in range(1, 6)])
    text = models.TextField('Текст отзыва')
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Отзыв от {self.user} — {self.apartment.name} ({self.rating}/5)'
