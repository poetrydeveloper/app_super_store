from django.core.exceptions import ValidationError
from django.contrib import admin
from django import forms
from .models import Request, RequestItem


class RequestItemForm(forms.ModelForm):
    class Meta:
        model = RequestItem
        fields = ['product', 'quantity', 'price_per_unit', 'supplier']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = self.fields['product'].queryset.filter(
            productunit__status='candidate_in_request'
        ).distinct()


class RequestItemInline(admin.TabularInline):
    model = RequestItem
    form = RequestItemForm
    extra = 0
    fields = ['product', 'quantity', 'price_per_unit', 'supplier', 'total_cost']
    readonly_fields = ['total_cost']


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    inlines = [RequestItemInline]
    list_display = ['id', 'created_at', 'total_products']
    list_filter = ['created_at']

    def total_products(self, obj):
        return sum(item.quantity for item in obj.items.all())

    total_products.short_description = 'Товаров'

    def save_model(self, request, obj, form, change):
        if not obj.items.exists():
            raise ValidationError("Добавьте хотя бы одну позицию")
        super().save_model(request, obj, form, change)