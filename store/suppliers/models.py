from django.db import models

class Supplier(models.Model):
    """Поставщик"""
    name = models.CharField('Наименование', max_length=255)
    contact_person = models.CharField(
        'Контактное лицо',
        max_length=255,
        blank=True,  # Разрешаем пустое значение в базе данных
        default=''   # Значение по умолчанию
    )
    phone = models.CharField(
        'Телефон',
        max_length=20,
        blank=True,  # Разрешаем пустое значение
        default=''   # Значение по умолчанию
    )
    notes = models.TextField('Примечания', blank=True)

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.contact_person})"