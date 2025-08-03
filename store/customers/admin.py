from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email_short', 'notes_short')
    search_fields = ('name', 'phone', 'email')
    list_filter = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'phone'),
            'description': 'Обязательные поля: Наименование и Телефон'
        }),
        ('Дополнительная информация', {
            'fields': ('email', 'notes'),
            'classes': ('collapse',)
        }),
    )

    def email_short(self, obj):
        return obj.email if obj.email else '-'

    email_short.short_description = 'Email'

    def notes_short(self, obj):
        return obj.notes[:50] + '...' if obj.notes else '-'

    notes_short.short_description = 'Примечания'