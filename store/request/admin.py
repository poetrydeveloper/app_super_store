from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db.models import Q
from .models import Request, RequestItem
from unit.models import ProductUnit


class RequestItemForm(forms.ModelForm):
    class Meta:
        model = RequestItem
        fields = ['product_unit', 'quantity', 'price_per_unit', 'supplier']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
            'price_per_unit': forms.NumberInput(attrs={'min': 0.01, 'step': 0.01})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = ProductUnit.objects.filter(status='candidate_in_request')

        if self.instance and self.instance.pk:
            queryset = queryset | ProductUnit.objects.filter(pk=self.instance.product_unit_id)

        self.fields['product_unit'].queryset = queryset.select_related('product').distinct()


class RequestItemInline(admin.TabularInline):
    model = RequestItem
    form = RequestItemForm
    extra = 1
    fields = ['product_unit', 'quantity', 'price_per_unit', 'supplier', 'total_cost']
    readonly_fields = ['total_cost']
    verbose_name = "Позиция заявки"
    min_num = 1

    def total_cost(self, obj):
        return f"{obj.total_cost:.2f} ₽" if obj.price_per_unit else "—"


@admin.register(RequestItem)
class RequestItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'request', 'product_unit', 'quantity', 'price_per_unit', 'supplier']
    list_filter = ['request', 'supplier']
    search_fields = ['product_unit__product__name']


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    inlines = [RequestItemInline]
    list_display = ['id', 'created_at', 'status_badge', 'total_units', 'total_amount', 'units_link']
    list_filter = ['created_at', 'is_completed']
    fieldsets = (
        (None, {'fields': ('is_completed', 'notes')}),
        ('Системная информация', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    readonly_fields = ['created_at']
    actions = ['mark_as_completed', 'mark_as_in_progress', 'view_units_in_request']

    def units_link(self, obj):
        url = reverse(
            'admin:unit_productunit_changelist') + f'?status=in_request&request_item__request__id__exact={obj.id}'
        return format_html('<a href="{}">Юниты ({})</a>', url, obj.items.count())

    units_link.short_description = 'Юниты'

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.request_id:
                instance.request = form.instance
            instance.save()

    def total_units(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def total_amount(self, obj):
        total = sum(item.total_cost for item in obj.items.all() if item.price_per_unit)
        return f"{total:.2f} ₽"

    def status_badge(self, obj):
        color = '#4CAF50' if obj.is_completed else '#FF9800'
        text = 'Завершена' if obj.is_completed else 'В работе'
        return format_html(
            '<span style="color:white;background:{};padding:2px 10px;border-radius:10px">{}</span>',
            color, text
        )

    @admin.action(description="✅ Отметить как завершенные")
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(is_completed=True)
        self.message_user(request, f"Отмечено {updated} заявок как завершенных", messages.SUCCESS)

    @admin.action(description="🔄 Вернуть в работу")
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(is_completed=False)
        self.message_user(request, f"{updated} заявок возвращены в работу", messages.SUCCESS)

    @admin.action(description="👀 Показать юниты в заявке")
    def view_units_in_request(self, request, queryset):
        from django.shortcuts import redirect
        if queryset.count() != 1:
            self.message_user(request, "Выберите ровно одну заявку", messages.ERROR)
            return

        request_id = queryset.first().id
        return redirect(reverse(
            'admin:unit_productunit_changelist') + f'?status=in_request&request_item__request__id__exact={request_id}')