from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime
from django.db import transaction
from django.utils.html import format_html
from django.urls import reverse


class ProductUnit(models.Model):
    STATUS_CHOICES = [
        ('create_empty', 'Создан пустым'),
        ('candidate_in_request', 'Кандидат на заявку'),
        ('in_request', 'В заявке'),
        ('in_request_cancelled', 'В заявке - отменен'),
        ('in_store', 'В магазине'),
        ('sold', 'Продан'),
        ('broken', 'Сломан'),
        ('lost', 'Утерян'),
        ('transferred', 'Передан'),
        ('extra_add_delivery', 'Экстренно вставлен в поставку'),
    ]

    # Основные поля
    product = models.ForeignKey(
        'goods.Product',
        on_delete=models.PROTECT,
        verbose_name='Товар',
        related_name='units'
    )
    serial_number = models.CharField(
        'Серийный номер',
        max_length=100,
        unique=True,
        blank=True
    )
    status = models.CharField(
        'Статус',
        max_length=25,
        choices=STATUS_CHOICES,
        default='create_empty'
    )
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    # Связи с документами
    # request_item = models.ForeignKey(
    #     'request.RequestItem',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     verbose_name='Позиция заявки'
    # )
    # delivery_item = models.ForeignKey(
    #     'delivery.DeliveryItem',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     verbose_name='Позиция поставки'
    # )
    is_extra_add_delivery_item = models.BooleanField(
        'Экстренная поставка (без заявки)',
        default=False
    )
    # sale_item = models.ForeignKey(
    #     'sale.SaleItem',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     verbose_name='Позиция продажи'
    # )

    # Поля продажи
    sale_date = models.DateField(
        'Дата продажи',
        null=True,
        blank=True
    )
    sale_price = models.DecimalField(
        'Цена продажи',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Единица товара'
        verbose_name_plural = 'Единицы товаров'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['sale_date']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.serial_number} ({self.get_status_display()})"

    # === Методы генерации и валидации ===
    @classmethod
    def generate_serial_number(cls, product):
        """Генерация уникального серийного номера формата: RF-{product_id}-{timestamp}-{random_part}"""
        if not product or not product.pk:
            raise ValidationError("Товар должен быть сохранён перед генерацией номера.")

        base_prefix = f"RF-{product.id}-"
        timestamp = datetime.now().strftime("%d%m%H%M%S")
        random_part = f"{datetime.now().microsecond:06d}"[:6]

        serial_number = f"{base_prefix}{timestamp}-{random_part}"

        if cls.objects.filter(serial_number=serial_number).exists():
            raise ValidationError("Не удалось сгенерировать уникальный серийный номер.")

        return serial_number

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Автоматическая генерация serial_number при создании"""
        if not self.pk and not self.serial_number:
            self.serial_number = self.generate_serial_number(self.product)
        super().save(*args, **kwargs)

    # === Методы для работы со статусами ===
    @transaction.atomic
    def safe_mark_as_sold(self, sale_item=None, sale_date=None, sale_price=None):
        """Безопасное помечение как проданного (вызывается из модели Sale)."""
        if self.status == 'sold':
            raise ValidationError("Товар уже продан.")

        self.status = 'sold'
        self.sale_item = sale_item
        self.sale_date = sale_date or datetime.now().date()
        self.sale_price = sale_price
        self.save()
        return self

    def get_purchase_price(self):
        """Возвращает цену закупки из связанной поставки."""
        if self.delivery_item:
            return self.delivery_item.price_per_unit
        return None

    # === Дополнительные свойства ===
    @property
    def purchase_price(self):
        """Свойство для отображения цены закупки (используется в админке)."""
        return self.get_purchase_price()

    @property
    def delivery_info(self):
        """Информация о поставке в виде словаря."""
        if not self.delivery_item:
            return None
        return {
            'date': self.delivery_item.delivery.delivery_date,
            'supplier': self.delivery_item.delivery.supplier.name,
            'price': self.delivery_item.price_per_unit
        }

    def clean(self):
        super().clean()
        self._validate_status_transitions()
        self._validate_document_links()
        self._validate_sale_fields()

    def _validate_status_transitions(self):
        """Проверка допустимых переходов между статусами."""
        if not self.pk:  # Новая запись - проверка не требуется
            return

        old_status = ProductUnit.objects.get(pk=self.pk).status
        new_status = self.status

        # Запрещённые переходы
        forbidden_transitions = {
            'sold': ['create_empty', 'candidate_in_request', 'in_request', 'in_request_cancelled'],
            'broken': ['sold'],
            'lost': ['sold'],
            'transferred': ['sold'],
        }

        if old_status in forbidden_transitions.get(new_status, []):
            raise ValidationError(
                {
                    'status': f'Нельзя перевести статус из "{self.get_status_display(old_status)}" в "{self.get_status_display()}"'}
            )

    def _validate_document_links(self):
        """Проверка согласованности связей с документами."""
        # Если товар в поставке - должна быть заполнена delivery_item
        if self.status == 'in_store' and not self.delivery_item:
            raise ValidationError(
                {'delivery_item': 'Для статуса "В магазине" должна быть указана поставка'}
            )

        # Если товар экстренно добавлен в поставку - должен быть флаг is_extra_add_delivery_item
        if self.status == 'extra_add_delivery' and not self.is_extra_add_delivery_item:
            raise ValidationError(
                {'is_extra_add_delivery_item': 'Для экстренной поставки флаг должен быть True'}
            )

    def _validate_sale_fields(self):
        """Проверка полей продажи."""
        if self.status == 'sold':
            if not self.sale_date:
                raise ValidationError(
                    {'sale_date': 'Для проданного товара укажите дату продажи'}
                )
            if not self.sale_price:
                raise ValidationError(
                    {'sale_price': 'Для проданного товара укажите цену продажи'}
                )
        else:
            if self.sale_date or self.sale_price:
                raise ValidationError(
                    {'status': 'Поля продажи заполнены, но статус не "sold"'}
                )