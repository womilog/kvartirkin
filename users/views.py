from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from apartments.models import Reservation
from .forms import RegistrationForm, LoginForm, ProfileEditForm


def auth_view(request):
    """Handle both login and registration on the same page."""
    login_form = LoginForm()
    register_form = RegistrationForm()
    active_tab = 'login'
    login_error = None
    register_error = None

    if request.method == 'POST':
        action = request.POST.get('action', 'login')

        if action == 'register':
            active_tab = 'register'
            # Преобразуем поля password1/password2 в password/password_confirm
            post_data = request.POST.copy()
            if 'password1' in post_data:
                post_data['password'] = post_data['password1']
            if 'password2' in post_data:
                post_data['password_confirm'] = post_data['password2']
            
            register_form = RegistrationForm(post_data)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                return redirect('index')
            else:
                # Получаем первую ошибку для отображения
                errors = []
                for field_errors in register_form.errors.values():
                    errors.extend(field_errors)
                register_error = errors[0] if errors else 'Исправьте ошибки в форме'

        elif action == 'login':
            active_tab = 'login'
            # Преобразуем поле phone в username для AuthenticationForm
            post_data = request.POST.copy()
            if 'phone' in post_data:
                post_data['username'] = post_data['phone']
            
            login_form = LoginForm(request, data=post_data)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                return redirect('index')
            else:
                login_error = 'Неверный телефон или пароль'

    context = {
        'login_form': login_form,
        'register_form': register_form,
        'reg_form': register_form,  # для совместимости с шаблоном
        'active_tab': active_tab,
        'login_error': login_error,
        'register_error': register_error,
        'show_register': active_tab == 'register',
    }
    return render(request, 'auth.html', context)


@login_required
def logout_view(request):
    """Log out the user."""
    logout(request)
    return redirect('index')


@login_required
def profile_view(request):
    """Display the user's profile, allow editing, and show booking history."""
    profile_form = ProfileEditForm(instance=request.user)
    password_form = PasswordChangeForm(user=request.user)
    # 'info' | 'password' — determines which panel is open after submission
    active_panel = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'edit_profile':
            profile_form = ProfileEditForm(request.POST, instance=request.user)
            active_panel = 'info'
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Данные профиля успешно обновлены.')
                return redirect('profile')

        elif action == 'change_password':
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            active_panel = 'password'
            if password_form.is_valid():
                user = password_form.save()
                # Keep the user logged in after password change
                update_session_auth_hash(request, user)
                messages.success(request, 'Пароль успешно изменён.')
                return redirect('profile')

    reservations = (
        Reservation.objects
        .filter(user=request.user)
        .select_related('apartment')
        .order_by('-created_at')
    )
    context = {
        'profile_user': request.user,
        'reservations': reservations,
        'profile_form': profile_form,
        'password_form': password_form,
        'active_panel': active_panel,
    }
    return render(request, 'profile.html', context)
