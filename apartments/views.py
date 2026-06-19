from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Avg
from django.http import JsonResponse
from .models import Apartment, Reservation, Review
from .forms import BookingForm
import pytz
from django.contrib.auth.decorators import login_required

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
        initial['first_name'] = request.user.first_name
        initial['last_name'] = request.user.last_name
        initial['phone'] = request.user.phone

    if request.method == 'POST':
        # Double-check bookings_enabled on POST
        if not apartment.bookings_enabled:
            messages.error(request, 'Бронирование временно недоступно для этих апартаментов.')
            return redirect('apartment_detail', slug=slug)
            
        form = BookingForm(request.POST, apartment=apartment)
        if form.is_valid():
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
            reservation.save()

            messages.success(request, 'Бронирование успешно создано!')
            return redirect('booking_success')
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = BookingForm(apartment=apartment, initial=initial)

    context = {
        'apartment': apartment,
        'form': form,
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
