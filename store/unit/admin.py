from django.contrib import admin
from django.utils.html import format_html
from .models import ProductUnit
from django.urls import reverse

@admin.register(ProductUnit)
class ProductUnitAdmin(admin.ModelAdmin):
    list_display = (
        'serial_number',
        'product_link',
        'status_badge',
        'purchase_price_display',
        'sale_info',
        'document_links',
        'created_at'
    )
    list_filter = (
        'status',
        'is_extra_add_delivery_item',
        'product__category',
        'created_at'
    )
    search_fields = (
        'serial_number',
        'product__name',
        'product__code'
    )
    readonly_fields = (
        'created_at',
        'serial_number',
        'purchase_price_display',
        'sale_info_detailed'
    )
    list_select_related = (
        'product',
        'request_item',
        'delivery_item',
        'sale_item'
    )
    fieldsets = (
        (None, {
            'fields': ('product', 'serial_number', 'status')
        }),
        ('Документы', {
            'fields': (
                'request_item',
                'delivery_item',
                'is_extra_add_delivery_item',
                'sale_item'
            ),
            'classes': ('collapse',)
        }),
        ('Продажа', {
            'fields': (
                'sale_date',
                'sale_price',
                'sale_info_detailed'
            ),
            'classes': ('collapse',)
        }),
        ('Системные', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    # === Кастомные методы для отображения ===
    def product_link(self, obj):
        url = reverse('admin:goods_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_link.short_description = 'Товар'
    product_link.admin_order_field = 'product'

    def status_badge(self, obj):
        colors = {
            'create_empty': 'gray',
            'candidate_in_request': 'lightblue',
            'in_request': 'blue',
            'in_request_cancelled': 'orange',
            'in_store': 'green',
            'sold': 'purple',
            'broken': 'red',
            'lost': 'darkorange',
            'transferred': 'teal',
            'extra_add_delivery': 'pink'
        }
        return format_html(
            '<span style="color: white; background: {}; padding: 3px 8px; border-radius: 10px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'

    def purchase_price_display(self, obj):
        price = obj.get_purchase_price()
        return f"{price} ₽" if price else "-"
    purchase_price_display.short_description = 'Цена закупки'

    def sale_info(self, obj):
        if obj.status == 'sold':
            date = obj.sale_date.strftime("%d.%m.%Y") if obj.sale_date else "N/A"
            price = f"{obj.sale_price} ₽" if obj.sale_price else "N/A"
            return format_html(
                '<span style="color: purple;">Продано: {} за {}</span>',
                date, price
            )
        return "-"
    sale_info.short_description = 'Продажа'

    def sale_info_detailed(self, obj):
        return self.sale_info(obj) if obj.status == 'sold' else "Не продано"
    sale_info_detailed.short_description = 'Детали продажи'

    def document_links(self, obj):
        links = []
        if obj.request_item:
            url = reverse('admin:warehouse_requestitem_change', args=[obj.request_item.id])
            links.append(f'<a href="{url}">Заявка</a>')
        if obj.delivery_item:
            url = reverse('admin:warehouse_deliveryitem_change', args=[obj.delivery_item.id])
            links.append(f'<a href="{url}">Поставка</a>')
        if obj.sale_item:
            url = reverse('admin:sale_saleitem_change', args=[obj.sale_item.id])
            links.append(f'<a href="{url}">Продажа</a>')
        return format_html(' | '.join(links)) if links else "-"
    document_links.short_description = 'Документы'

    def save_model(self, request, obj, form, change):
        obj.full_clean()  # Вызывает clean()
        super().save_model(request, obj, form, change)