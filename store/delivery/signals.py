# signals.py (дополнительно)
from datetime import timezone

from django.db.models.signals import post_save
from django.dispatch import receiver
from unit.models import ProductUnit

from store.delivery.models import DeliveryItem


@receiver(post_save, sender=DeliveryItem)
def update_product_units(sender, instance, created, **kwargs):
    """Обновление статусов единиц товара при изменении DeliveryItem"""
    if instance.delivery.is_confirmed:
        # Перевод единиц в статус in_store
        ProductUnit.objects.filter(
            delivery_item=instance,
            status__in=['in_delivery', 'extra_add_delivery']
        ).update(
            status='in_store',
            store_arrival_date=timezone.now()
        )