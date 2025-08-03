from django.db import models
from django.core.validators import RegexValidator

class Customer(models.Model):
    """Клиент (покупатель)"""
    name = models.CharField(
        'Наименование',
        max_length=255,
        help_text='Полное наименование клиента'
    )
    phone = models.CharField(
        'Телефон',
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Формат: +999999999. До 15 цифр.'
            )
        ]
    )
    email = models.EmailField(
        'Email',
        blank=True,
        null=True,
        help_text='Необязательное поле'
    )
    notes = models.TextField(
        'Примечания',
        blank=True,
        null=True,
        help_text='Дополнительная информация'
    )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone})"