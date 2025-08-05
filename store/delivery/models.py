# models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Delivery(models.Model):
    """Модель поставки товаров"""
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.PROTECT,
        verbose_name='Поставщик'
    )
    delivery_date = models.DateField('Дата поставки', default=timezone.now)
    is_confirmed = models.BooleanField('Подтверждена', default=False)
    notes = models.TextField('Примечания', blank=True)

    class Meta:
        verbose_name = 'Поставка'
        verbose_name_plural = 'Поставки'
        ordering = ['-delivery_date']

    def __str__(self):
        return f"Поставка #{self.id} от {self.delivery_date}"

    def clean(self):
        if self.delivery_date > timezone.now().date():
            raise ValidationError('Дата поставки не может быть в будущем')


class DeliveryItem(models.Model):
    """Позиции в поставке"""
    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Поставка'
    )
    product = models.ForeignKey(
        'goods.Product',
        on_delete=models.PROTECT,
        verbose_name='Товар'
    )
    request_item = models.ForeignKey(
        'request.RequestItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Связанная заявка'
    )
    quantity_expected = models.PositiveIntegerField(
        'Ожидаемое количество',
        default=0
    )
    quantity_received = models.PositiveIntegerField(
        'Фактически получено',
        default=0
    )
    price_per_unit = models.DecimalField(
        'Цена за единицу',
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        verbose_name = 'Позиция поставки'
        verbose_name_plural = 'Позиции поставок'
        ordering = ['delivery', 'product']

    def __str__(self):
        return f"{self.product.name} | Ожидаем: {self.quantity_expected} | Получено: {self.quantity_received}"

    def clean(self):
        if self.quantity_received < 0:
            raise ValidationError('Количество не может быть отрицательным')

        if self.request_item and self.quantity_expected != self.request_item.quantity:
            raise ValidationError('Несоответствие количеству в заявке')

    def save(self, *args, **kwargs):
        if self.request_item:
            self.quantity_expected = self.request_item.quantity
        super().save(*args, **kwargs)

    def process_units(self):
        """Обработка единиц товара при подтверждении поставки"""
        from unit.models import ProductUnit

        # Получаем единицы из заявки
        requested_units = ProductUnit.objects.filter(
            status='in_request',
            product=self.product
        )[:self.quantity_received]

        # Обновляем полученные единицы
        requested_units.update(
            status='in_delivery',
            delivery_date=self.delivery.delivery_date,
            delivery_item=self
        )

        # Обрабатываем излишки
        if self.quantity_received > self.quantity_expected:
            extra_count = self.quantity_received - self.quantity_expected
            extra_units = [
                ProductUnit(
                    product=self.product,
                    status='extra_add_delivery',
                    delivery_date=self.delivery.delivery_date,
                    delivery_item=self
                ) for _ in range(extra_count)
            ]
            ProductUnit.objects.bulk_create(extra_units)


@receiver(post_save, sender=Delivery)
def update_delivery_status(sender, instance, **kwargs):
    """Сигнал для подтверждения поставки"""
    if instance.is_confirmed:
        for item in instance.items.all():
            item.process_units()
