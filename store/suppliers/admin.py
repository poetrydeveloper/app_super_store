from django.contrib import admin
from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'notes_short')
    search_fields = ('name', 'contact_person', 'phone')

    fieldsets = (
        (None, {
            'fields': ('name', ('contact_person', 'phone'), 'notes'),
            'description': 'Только поле "Наименование" является обязательным'
        }),
    )

    def notes_short(self, obj):
        return obj.notes[:50] + '...' if obj.notes else '-'

    notes_short.short_description = 'Примечания'