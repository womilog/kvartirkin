from django.contrib import admin
from users.admin_site import custom_admin_site, CustomModelAdmin
from .models import Apartment, ApartmentImage, Reservation, Review


class ApartmentImageInline(admin.TabularInline):
    model = ApartmentImage
    extra = 3
    ordering = ['order']

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_add_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff


@admin.register(Apartment, site=custom_admin_site)
class ApartmentAdmin(CustomModelAdmin):
    list_display = ('name', 'address', 'rooms', 'area', 'price_per_day', 'is_active', 'bookings_enabled')
    list_filter = ('is_active', 'bookings_enabled', 'has_wifi', 'has_smart_tv', 'has_washing_machine', 'has_ac', 'pets_allowed')
    search_fields = ('name', 'address')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ApartmentImageInline]
    list_editable = ('is_active', 'bookings_enabled')

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'address', 'description', 'is_active', 'bookings_enabled')
        }),
        ('Параметры', {
            'fields': ('rooms', 'area', 'price_per_day', 'max_guests', 'distance_to_sea')
        }),
        ('Координаты', {
            'fields': ('latitude', 'longitude')
        }),
        ('Удобства', {
            'fields': ('has_wifi', 'has_smart_tv', 'has_washing_machine', 'has_ac', 'pets_allowed')
        }),
    )


@admin.register(Reservation, site=custom_admin_site)
class ReservationAdmin(CustomModelAdmin):
    list_display = ('apartment', 'first_name', 'last_name', 'phone', 'check_in', 'check_out', 'guests', 'total_price', 'status')
    list_filter = ('status', 'apartment')
    search_fields = ('first_name', 'last_name', 'phone')
    list_editable = ('status',)
    date_hierarchy = 'check_in'

    fieldsets = (
        ('Апартаменты', {
            'fields': ('apartment', 'user')
        }),
        ('Контактные данные', {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        ('Детали бронирования', {
            'fields': ('check_in', 'check_out', 'guests', 'has_pet', 'comment')
        }),
        ('Оплата', {
            'fields': ('total_price', 'status')
        }),
    )


@admin.register(Review, site=custom_admin_site)
class ReviewAdmin(CustomModelAdmin):
    list_display = ('apartment', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'apartment')
    search_fields = ('text', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at',)