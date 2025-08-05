from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q
from .models import ProductUnit


class StatusFilter(admin.SimpleListFilter):
    """Фильтр по группам статусов"""
    title = 'Группа статусов'
    parameter_name = 'status_group'

    def lookups(self, request, model_admin):
        return (
            ('available', 'Доступные для заявки'),
            ('in_process', 'В обработке'),
            ('completed', 'Завершенные'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'available':
            return queryset.filter(
                Q(status='created') | Q(status='candidate_in_request'))
        if self.value() == 'in_process':
            return queryset.filter(
                Q(status='in_request') | Q(status='in_delivery'))
        if self.value() == 'completed':
            return queryset.filter(
                Q(status='in_store') | Q(status='sold') | Q(status='transferred'))


class CandidateFilter(admin.SimpleListFilter):
    """Фильтр для работы с кандидатами"""
    title = 'Кандидаты'
    parameter_name = 'candidates'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Только кандидаты'),
            ('no', 'Исключить кандидатов'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(status='candidate_in_request')
        if self.value() == 'no':
            return queryset.exclude(status='candidate_in_request')


@admin.register(ProductUnit)
class ProductUnitAdmin(admin.ModelAdmin):
    list_display = (
        'serial_number',
        'product_link',
        'status_badge',
        'is_candidate',
        'purchase_price_display',
        'request_link',
        'document_links',
        'created_at'
    )
    list_display_links = ('serial_number', 'product_link')
    list_filter = (CandidateFilter, StatusFilter, 'status', 'product__category', 'request_item__request')
    search_fields = ('serial_number', 'product__name', 'product__code', 'request_item__request__id')
    readonly_fields = ('created_at', 'updated_at', 'request_info')
    actions = [
        'mark_as_candidates',
        'create_request_from_candidates',
        'reset_to_created_status',
        'link_to_request'
    ]

    fieldsets = (
        ('Основная информация', {
            'fields': ('product', 'serial_number', 'status')
        }),
        ('Документы', {
            'fields': ('request_item', 'request_info', 'delivery_item'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Методы для отображения в списке
    def product_link(self, obj):
        if obj.product:
            url = reverse('admin:goods_product_change', args=[obj.product.id])
            return format_html(
                '<a href="{}">{} <small>({})</small></a>',
                url, obj.product.name, obj.product.code
            )
        return "-"

    product_link.short_description = 'Товар'
    product_link.admin_order_field = 'product__name'

    def status_badge(self, obj):
        status_colors = {
            'created': '#9e9e9e',
            'candidate_in_request': '#42a5f5',
            'in_request': '#1976d2',
            'in_delivery': '#7e57c2',
            'in_store': '#388e3c',
            'sold': '#8e24aa',
            'broken': '#e53935',
            'lost': '#fb8c00',
            'transferred': '#00897b',
            'extra_add_delivery': '#f06292'
        }
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:10px">{}</span>',
            status_colors.get(obj.status, '#9e9e9e'),
            obj.get_status_display()
        )

    status_badge.short_description = 'Статус'
    status_badge.admin_order_field = 'status'

    def is_candidate(self, obj):
        return obj.status == 'candidate_in_request'

    is_candidate.boolean = True
    is_candidate.short_description = 'Кандидат?'

    def purchase_price_display(self, obj):
        if hasattr(obj, 'get_purchase_price'):
            price = obj.get_purchase_price()
            return f"{price} ₽" if price else "-"
        return "-"

    purchase_price_display.short_description = 'Цена'

    def document_links(self, obj):
        links = []
        if obj.request_item:
            url = reverse('admin:request_requestitem_change', args=[obj.request_item.id])
            links.append(f'<a href="{url}">📝 Заявка</a>')
        if obj.delivery_item:
            url = reverse('admin:warehouse_deliveryitem_change', args=[obj.delivery_item.id])
            links.append(f'<a href="{url}">🚚 Поставка</a>')
        return format_html(' '.join(links)) if links else "-"

    document_links.short_description = 'Документы'

    def request_link(self, obj):
        if obj.request_item:
            url = reverse('admin:request_request_change', args=[obj.request_item.request.id])
            return format_html(
                '<a href="{}">📋 Заявка #{}</a>',
                url,
                obj.request_item.request.id
            )
        return "-"

    request_link.short_description = 'Заявка'

    def request_info(self, obj):
        if obj.request_item:
            url = reverse('admin:request_request_change', args=[obj.request_item.request.id])
            return format_html(
                '<a href="{}">Заявка #{}</a> ({} позиций)',
                url,
                obj.request_item.request.id,
                obj.request_item.request.items.count()
            )
        return "-"

    request_info.short_description = 'Информация о заявке'

    # Действия
    @admin.action(description="🟢 Пометить как кандидатов")
    def mark_as_candidates(self, request, queryset):
        valid_statuses = ['created', 'in_request_cancelled', 'create_empty']
        valid_units = queryset.filter(status__in=valid_statuses)

        if not valid_units.exists():
            self.message_user(request, "Нет подходящих единиц", messages.WARNING)
            return

        updated = valid_units.update(status='candidate_in_request')
        self.message_user(
            request,
            f"Обновлено {updated} единиц",
            messages.SUCCESS
        )

    @admin.action(description="📌 Привязать к заявке")
    def link_to_request(self, request, queryset):
        from django.shortcuts import render
        from request.models import Request

        candidates = queryset.filter(status='candidate_in_request')
        if not candidates.exists():
            self.message_user(request, "Только кандидаты могут быть привязаны", messages.WARNING)
            return

        active_requests = Request.objects.filter(is_completed=False).order_by('-created_at')
        return render(
            request,
            'admin/unit/link_to_request.html',
            context={
                'units': candidates,
                'requests': active_requests,
                'opts': self.model._meta,
            }
        )

    @admin.action(description="📝 Создать заявку из кандидатов")
    def create_request_from_candidates(self, request, queryset):
        from request.models import Request, RequestItem
        candidates = queryset.filter(status='candidate_in_request')

        if not candidates.exists():
            self.message_user(request, "Нет кандидатов", messages.WARNING)
            return

        request_obj = Request.objects.create(
            notes=f"Автоматически создана из {candidates.count()} кандидатов"
        )

        for unit in candidates:
            RequestItem.objects.create(
                request=request_obj,
                product_unit=unit,
                quantity=1,
                price_per_unit=unit.get_purchase_price() or 0,
                supplier=unit.product.main_supplier if hasattr(unit, 'product') else None
            )
            unit.status = 'in_request'
            unit.save()

        self.message_user(
            request,
            f"Создана заявка #{request_obj.id} с {candidates.count()} позициями",
            messages.SUCCESS
        )
        return HttpResponseRedirect(reverse('admin:request_request_change', args=[request_obj.id]))

    @admin.action(description="🔄 Сбросить статус")
    def reset_to_created_status(self, request, queryset):
        queryset.update(status='created')
        self.message_user(request, "Статусы сброшены", messages.SUCCESS)