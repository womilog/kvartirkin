import logging
from datetime import date, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from .forms import BookingForm
from .models import Apartment, Reservation, Review

logger = logging.getLogger(__name__)


def _send_booking_request_email(reservation, request):
    """Send a booking request notification to the landlord.

    The email is plain-text by default; if a template exists it is also
    rendered as HTML. Failures are logged but never block the user flow.
    """
    apartment = reservation.apartment
    subject = (
        f'Новая заявка на бронирование: {apartment.name} '
        f'({reservation.check_in:%d.%m.%Y} — {reservation.check_out:%d.%m.%Y})'
    )
    admin_url = request.build_absolute_uri(
        reverse('admin:apartments_reservation_change', args=[reservation.pk])
    )
    nights = (reservation.check_out - reservation.check_in).days

    context = {
        'reservation': reservation,
        'apartment': apartment,
        'nights': nights,
        'admin_url': admin_url,
    }

    body_lines = [
        'Поступила новая заявка на бронирование.',
        '',
        f'Апартаменты: {apartment.name}',
        f'Адрес: {apartment.address}',
        '',
        f'Заезд:  {reservation.check_in:%d.%m.%Y}',
        f'Выезд:  {reservation.check_out:%d.%m.%Y}',
        f'Ночей:  {nights}',
        f'Гостей: {reservation.guests}'
        f'{" (с питомцем)" if reservation.has_pet else ""}',
        '',
        'Гость:',
        f'  Имя:     {reservation.first_name} {reservation.last_name}',
        f'  Телефон: {reservation.phone}',
    ]
    if reservation.user_id and getattr(reservation.user, 'email', ''):
        body_lines.append(f'  Email:   {reservation.user.email}')
    if reservation.comment:
        body_lines += ['', 'Комментарий гостя:', reservation.comment]
    body_lines += [
        '',
        f'Ориентировочная стоимость: {reservation.total_price} ₽',
        '',
        f'Подтвердить или отклонить заявку: {admin_url}',
    ]
    text_body = '\n'.join(body_lines)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.LANDLORD_EMAIL],
            reply_to=[reservation.user.email] if (
                reservation.user_id and getattr(reservation.user, 'email', '')
            ) else None,
        )
        # Attach HTML version if a template is provided.
        try:
            html_body = render_to_string(
                'emails/booking_request.html', context
            )
            msg.attach_alternative(html_body, 'text/html')
        except Exception:
            pass
        msg.send(fail_silently=False)
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            'Failed to send booking-request email for reservation #%s: %s',
            reservation.pk, exc,
        )

# utc_zone = pytz.utc
# moscow_tz = pytz.timezone('Europe/Moscow')

def index(request):
    """Home page — show available apartments carousel."""
    from datetime import date
    apartments = Apartment.objects.filter(is_active=True).order_by('name')
    
    # Add current availability to each apartment
    today = date.today()
    apartments_with_availability = []
    for apt in apartments:
        res_now = False
        for res in apt.reservations.all():
            if res.check_in <= today <= res.check_out :
                # aware_dt_start = utc_zone.localize(res.check_in)
                # moscow_time_start = aware_dt_start.astimezone(moscow_tz).strftime('%Y-%m-%d')
                
                # aware_dt_end = utc_zone.localize(res.check_out)
                # moscow_time_end = aware_dt_end.astimezone(moscow_tz).strftime('%Y-%m-%d')

                res_now = f"Занято с {res.check_in.strftime('%m-%d-%Y')} по {res.check_out.strftime('%m-%d-%Y')}"

        apartments_with_availability.append({
            'apartment': apt,
            'is_available': apt.get_current_availability(),
            'res_now' : res_now
        })
    
    context = {
        'apartments': apartments_with_availability,
    }
    return render(request, 'index.html', context)


def apartment_list(request):
    """List all active apartments."""
    from datetime import date
    apartments = Apartment.objects.filter(is_active=True).order_by('name')
    
    # Add current availability to each apartment
    apartments_with_availability = []
    for apt in apartments:
        apartments_with_availability.append({
            'apartment': apt,
            'is_available': apt.get_current_availability(),
        })
    
    context = {
        'apartments': apartments_with_availability,
    }
    return render(request, 'apartments.html', context)


def apartment_detail(request, slug):
    """Detail page for a single apartment."""
    apartment = get_object_or_404(Apartment, slug=slug, is_active=True)
    images = apartment.images.all()
    reviews = apartment.reviews.select_related('user').all()

    # Calculate average rating
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    avg_rating = round(avg_rating, 1)

    # Get reservations for availability check
    reservations = Reservation.objects.filter(
        apartment=apartment,
        status__in=['pending', 'confirmed'],
        check_out__gte=date.today(),
    ).order_by('check_in')
    
    # Check current availability
    is_available = apartment.get_current_availability()

    context = {
        'apartment': apartment,
        'images': images,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': reviews.count(),
        'reservations': reservations,
        'is_available': is_available,
    }
    return render(request, 'apartment_detail.html', context)


@login_required
def booking(request, slug):
    """Booking page for an apartment."""
    apartment = get_object_or_404(Apartment, slug=slug, is_active=True)
    
    # Check if bookings are enabled for this apartment
    if not apartment.bookings_enabled:
        messages.error(request, 'Бронирование временно недоступно для этих апартаментов.')
        return redirect('apartment_detail', slug=slug)

        # Pre-fill dates from query params
    initial = {}
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')
    if check_in:
        initial['check_in'] = check_in
    if check_out:
        initial['check_out'] = check_out

    # Pre-fill user info if logged in
    if request.user.is_authenticated:
        initial.setdefault('first_name', request.user.first_name or '')
        initial.setdefault('last_name', request.user.last_name or '')
        initial.setdefault('phone', getattr(request.user, 'phone', '') or '')

    if request.method == 'POST':
        # Double-check bookings_enabled on POST
        if not apartment.bookings_enabled:
            messages.error(request, 'Бронирование временно недоступно для этих апартаментов.')
            return redirect('apartment_detail', slug=slug)

        form = BookingForm(request.POST, apartment=apartment)
        if form.is_valid():
            # Wrap creation in a transaction so a race-condition double-booking
            # is prevented at DB level (combined with form.clean overlap check).
            with transaction.atomic():
                reservation = form.save(commit=False)
                reservation.apartment = apartment
                if request.user.is_authenticated:
                    reservation.user = request.user

                # Calculate total price
                nights = (reservation.check_out - reservation.check_in).days
                price_per_night = apartment.price_per_day
                if reservation.has_pet:
                    price_per_night += 500  # pet surcharge per day
                reservation.total_price = nights * price_per_night

                # Request-based workflow: always start as 'pending'.
                # Pending reservations already block dates (see model & form).
                reservation.status = 'pending'
                reservation.save()

            # Notify the landlord by email (non-blocking on failure).
            _send_booking_request_email(reservation, request)

            messages.success(
                request,
                'Ваша заявка отправлена! Мы свяжемся с вами для подтверждения.',
            )
            return redirect('booking_success')
        else:
            # Only surface non-field errors as flash messages — per-field errors
            # are already shown inline next to the inputs in the template.
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = BookingForm(apartment=apartment, initial=initial)

    # Build the list of currently-blocking reservations so the template can
    # show the user which dates are already taken. Only reservations whose
    # check-out is today or later still matter for new bookings.
    today = date.today()
    occupied_reservations = apartment.reservations.filter(
        status__in=['pending', 'confirmed'],
        check_out__gte=today,
    ).order_by('check_in').values('check_in', 'check_out')

    occupied_ranges = [
        {
            'check_in': r['check_in'],
            'check_out': r['check_out'],
        }
        for r in occupied_reservations
    ]
    # JSON-safe version for the small client-side overlap warning.
    occupied_ranges_json = [
        {
            'check_in': r['check_in'].isoformat(),
            'check_out': r['check_out'].isoformat(),
        }
        for r in occupied_ranges
    ]

    context = {
        'apartment': apartment,
        'form': form,
        'occupied_ranges': occupied_ranges,
        'occupied_ranges_json': occupied_ranges_json,
    }
    return render(request, 'booking.html', context)


def booking_success(request):
    """Page shown after successful booking."""
    return render(request, 'booking_success.html')


def check_availability(request, slug):
    """AJAX endpoint to check if apartment is available for specific dates."""
    apartment = get_object_or_404(Apartment, slug=slug, is_active=True)
    
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')
    
    if not check_in or not check_out:
        return JsonResponse({
            'available': False,
            'error': 'Необходимо указать даты заезда и выезда'
        })
    
    try:
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({
            'available': False,
            'error': 'Неверный формат дат'
        })
    
    # Check if dates are valid
    if check_out_date <= check_in_date:
        return JsonResponse({
            'available': False,
            'error': 'Дата выезда должна быть позже даты заезда'
        })
    
    # Check availability
    is_available = apartment.is_available_for_dates(check_in_date, check_out_date)
    
    if is_available:
        # Calculate price
        nights = (check_out_date - check_in_date).days
        total = nights * apartment.price_per_day
        return JsonResponse({
            'available': True,
            'nights': nights,
            'total_price': int(total)
        })
    else:
        return JsonResponse({
            'available': False,
            'error': 'Выбранные даты уже заняты'
        })
