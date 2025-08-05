# admin.py
from django.contrib import admin
from .models import Delivery, DeliveryItem

class DeliveryItemInline(admin.TabularInline):
    model = DeliveryItem
    extra = 0
    fields = ('product', 'request_item', 'quantity_expected', 'quantity_received', 'price_per_unit')
    readonly_fields = ('quantity_expected',)
    raw_id_fields = ('product', 'request_item')

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'delivery_date', 'supplier', 'status', 'total_products')
    list_filter = ('delivery_date', 'supplier', 'is_confirmed')
    search_fields = ('id', 'supplier__name')
    date_hierarchy = 'delivery_date'
    inlines = (DeliveryItemInline,)
    actions = ('confirm_delivery',)

    def status(self, obj):
        return "Подтверждена" if obj.is_confirmed else "Ожидает"
    status.short_description = 'Статус'

    def total_products(self, obj):
        return obj.items.count()
    total_products.short_description = 'Товаров'

    def confirm_delivery(self, request, queryset):
        queryset.update(is_confirmed=True)
    confirm_delivery.short_description = "Подтвердить выбранные поставки"

@admin.register(DeliveryItem)
class DeliveryItemAdmin(admin.ModelAdmin):
    list_display = ('delivery', 'product', 'quantity_expected', 'quantity_received', 'status')
    list_filter = ('delivery__delivery_date', 'product')
    raw_id_fields = ('product', 'request_item')

    def status(self, obj):
        if obj.quantity_received == 0:
            return "Не получено"
        elif obj.quantity_received < obj.quantity_expected:
            return "Частично"
        elif obj.quantity_received == obj.quantity_expected:
            return "Полностью"
        else:
            return "С излишком"
    status.short_description = 'Статус'