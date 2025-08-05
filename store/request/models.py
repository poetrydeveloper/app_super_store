#app request  models
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
    product = models.ForeignKey('goods.Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.pk:  # Только при создании
            self._create_units()
        super().save(*args, **kwargs)

    def _create_units(self):
        """Создает недостающие unit и связывает их"""
        from unit.models import ProductUnit

        candidates = ProductUnit.objects.filter(
            product=self.product,
            status='candidate_in_request',
            request_item__isnull=True
        )[:self.quantity]

        needed_units = self.quantity - candidates.count()
        if needed_units > 0:
            if not self.product.code:
                raise ValidationError("Нельзя создать unit без кода товара")

            new_units = [
                ProductUnit(
                    product=self.product,
                    status='candidate_in_request',
                    serial_number=f"{self.product.code}-{timezone.now().strftime('%Y%m%d')}-{i:03d}"
                ) for i in range(1, needed_units + 1)
            ]
            ProductUnit.objects.bulk_create(new_units)
            all_units = list(candidates) + new_units
        else:
            all_units = list(candidates)

        ProductUnit.objects.filter(pk__in=[u.pk for u in all_units]).update(
            status='in_request',
            request_item=self
        )

    @property
    def total_cost(self):
        return self.price_per_unit * self.quantity

    def clean(self):
        if self.price_per_unit <= 0:
            raise ValidationError("Цена должна быть положительной")
        if self.quantity < 1:
            raise ValidationError("Количество не может быть меньше 1")

    def __str__(self):
        return f"{self.product.name} x{self.quantity} ({self.price_per_unit} ₽)"