from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import secrets

from apartments.models import Reservation
from .forms import (
    CustomPasswordChangeForm,
    RegistrationForm,
    LoginForm,
    ProfileEditForm,
    RequestPasswordResetForm,
    ResetPasswordForm,
)
from .models import CustomUser, PasswordResetToken


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
    password_form = CustomPasswordChangeForm(user=request.user)
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
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
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


def request_password_reset(request):
    """Send a password reset link to the user's email."""
    if request.method != 'POST':
        return redirect('auth')

    form = RequestPasswordResetForm(request.POST)
    if not form.is_valid():
        errors = []
        for field_errors in form.errors.values():
            errors.extend(field_errors)
        register_error = errors[0] if errors else 'Укажите корректный email'
        return redirect('auth') + '?tab=password_reset&error=' + register_error

    email = form.cleaned_data['email']
    user = CustomUser.objects.get(email__iexact=email)

    # Invalidate previous unused tokens
    PasswordResetToken.objects.filter(
        user=user,
        used=False,
    ).update(used=True)

    # Generate token
    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken.objects.create(user=user, token=token)

    # Build reset link
    reset_url = request.build_absolute_uri(
        reverse('password_reset_confirm', kwargs={
            'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': reset_token.token,
        })
    )

    # Send email
    subject = 'Восстановление пароля — Квартиркинъ'
    message = (
        f'Здравствуйте, {user.first_name}!\n\n'
        f'Вы запросили восстановление пароля на сайте Квартиркинъ.\n'
        f'Перейдите по следующей ссылке для создания нового пароля:\n'
        f'{reset_url}\n\n'
        f'Ссылка действительна в течение 1 часа.\n\n'
        f'Если вы не запрашивали восстановление пароля, проигнорируйте это письмо.\n\n'
        f'С уважением,\nКвартиркинъ'
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        messages.error(request, 'Не удалось отправить письмо. Попробуйте позже.')
        return redirect('auth')

    messages.success(
        request,
        'Письмо с инструкциями по восстановлению пароля отправлено на ' + email,
    )
    return redirect('auth')


def password_reset_confirm(request, uidb64, token):
    """Allow the user to set a new password using the reset token."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is None:
        messages.error(request, 'Неверная ссылка для восстановления пароля.')
        return redirect('auth')

    try:
        reset_token = PasswordResetToken.objects.get(
            user=user,
            token=token,
        )
    except PasswordResetToken.DoesNotExist:
        reset_token = None

    if reset_token is None:
        messages.error(request, 'Неверный токен восстановления пароля.')
        return redirect('auth')

    if reset_token.is_expired():
        messages.error(request, 'Ссылка для восстановления пароля истекла. Запросите новую.')
        return redirect('auth')

    if reset_token.used:
        messages.error(request, 'Эта ссылка уже была использована. Запросите новую.')
        return redirect('auth')

    form = ResetPasswordForm(user=user)

    if request.method == 'POST':
        form = ResetPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            reset_token.used = True
            reset_token.save()
            messages.success(
                request,
                'Пароль успешно изменён. Теперь вы можете войти в аккаунт.',
            )
            return redirect('auth')

    context = {
        'form': form,
    }
    return render(request, 'password_reset_confirm.html', context)
