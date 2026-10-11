# Generated manually on 2026-06-20

from django.db import migrations, models

def convert_smoke_forward(apps, schema_editor):
    Apartment = apps.get_model('apartments', 'Apartment')
    # Старое поле было BooleanField: False -> zapret, True -> balcony
    Apartment.objects.filter(avaible_smoke='False').update(avaible_smoke='zapret')
    Apartment.objects.filter(avaible_smoke='True').update(avaible_smoke='zapret') # на всякий случай строковые значения
    # Для нативных boolean в SQLite/Postgres может быть 0/1
    # Если у тебя Postgres, раскомментируй:
    # for obj in Apartment.objects.all():
    #     if obj.avaible_smoke is False or obj.avaible_smoke == 'False' or obj.avaible_smoke == '0':
    #         obj.avaible_smoke = 'zapret'
    #     elif obj.avaible_smoke is True or obj.avaible_smoke == 'True' or obj.avaible_smoke == '1':
    #         obj.avaible_smoke = 'balcony'
    #         obj.save()

def convert_smoke_backward(apps, schema_editor):
    Apartment = apps.get_model('apartments', 'Apartment')
    Apartment.objects.filter(avaible_smoke='zapret').update(avaible_smoke=False)
    Apartment.objects.exclude(avaible_smoke='zapret').update(avaible_smoke=True)


class Migration(migrations.Migration):

    dependencies = [
        ('apartments', '0005_alter_reservation_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='apartment',
            name='city',
            field=models.CharField(choices=[('Vorkuta', 'Воркута'), ('Gelendzhik', 'Геленджик')], default='Vorkuta', max_length=20, verbose_name='город'),
        ),
        migrations.AddField(
            model_name='apartment',
            name='distance_to_center',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Расстояние до центра Города'),
        ),
        migrations.AlterField(
            model_name='apartment',
            name='avaible_smoke',
            field=models.CharField(choices=[('zapret', 'Запрещено'), ('balcony', 'На балконе'), ('entrance', 'В подъезде')], default='zapret', max_length=20, verbose_name='Разрешено курить'),
        ),
        # Конвертация старых данных Boolean -> Char
        migrations.RunPython(convert_smoke_forward, convert_smoke_backward),
    ]