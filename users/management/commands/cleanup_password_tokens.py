from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from users.models import PasswordResetToken


class Command(BaseCommand):
    help = 'Удалить истекшие токены восстановления пароля старше 7 дней'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Удалять токены старше указанного количества дней (по умолчанию: 7)',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)

        # Помечаем все истекшие токены как used
        expired_tokens = PasswordResetToken.objects.filter(
            expires_at__lt=timezone.now(),
            used=False,
        )
        expired_count = expired_tokens.count()
        if expired_count > 0:
            expired_tokens.update(used=True)
            self.stdout.write(
                self.style.WARNING(f'Помечено как использованные {expired_count} истекших токенов')
            )

        # Удаляем токены старше N дней
        old_tokens = PasswordResetToken.objects.filter(
            expires_at__lt=cutoff_date,
        )
        deleted_count, _ = old_tokens.delete()

        self.stdout.write(
            self.style.SUCCESS(f'Удалено {deleted_count} токенов старше {days} дней')
        )
