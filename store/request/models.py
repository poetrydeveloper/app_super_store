from datetime import timezone
from django.db import models
from django.core.exceptions import ValidationError

class Request(models.Model):
    """Заявка (заголовок)"""
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    is_completed = models.BooleanField('Выполнена', default=False)
    notes = models.TextField('Примечания', blank=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка #{self.id}"


class RequestItem(models.Model):
    request = models.ForeignKey('Request', on_delete=models.CASCADE, related_name='items')
    product_unit = models.ForeignKey('unit.ProductUnit', on_delete=models.PROTECT)  # Изменено с product на product_unit
    quantity = models.PositiveIntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    @property
    def product(self):
        """Для обратной совместимости с кодом, ожидающим product"""
        return self.product_unit.product

    def save(self, *args, **kwargs):
        if not self.pk:  # Только при создании
            self._update_unit_status()
        super().save(*args, **kwargs)

    def _update_unit_status(self):
        """Обновляет статус product_unit"""
        if self.product_unit.status != 'in_request':
            self.product_unit.status = 'in_request'
            self.product_unit.save()

    @property
    def total_cost(self):
        return self.price_per_unit * self.quantity

    def clean(self):
        if self.price_per_unit <= 0:
            raise ValidationError("Цена должна быть положительной")
        if self.quantity < 1:
            raise ValidationError("Количество не может быть меньше 1")

    def __str__(self):
        return f"{self.product_unit.product.name} x{self.quantity} ({self.price_per_unit} ₽)"