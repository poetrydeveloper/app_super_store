# app goods/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.text import slugify
from .models import Category, Product
from files.models import ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_main')  # Убрали поле code из отображения
    readonly_fields = ('code_preview', 'created_short')  # Добавили код только для чтения

    def code_preview(self, obj):
        return obj.product.code if obj.product else '—'
    code_preview.short_description = 'Код товара'

    def created_short(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M') if obj.created_at else ''
    created_short.short_description = 'Создано'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_link', 'slug_display', 'product_count')
    list_filter = ('parent',)
    search_fields = ('name',)
    fields = ('name', 'parent')

    def parent_link(self, obj):
        if obj.parent:
            return format_html('<a href="../{}/">{}</a>', obj.parent.id, obj.parent.name)
        return "-"
    parent_link.short_description = 'Родительская категория'

    def slug_display(self, obj):
        return obj.slug or "Не сгенерирован"
    slug_display.short_description = 'ЧПУ'

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Товаров'

    def save_model(self, request, obj, form, change):
        if not obj.slug:
            base_slug = slugify(obj.name)
            unique_slug = base_slug
            counter = 1

            while Category.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1

            obj.slug = unique_slug
        super().save_model(request, obj, form, change)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'main_image_preview', 'images_count')
    readonly_fields = ('main_image_preview', 'images_list', 'add_images')
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'name', 'category')
        }),
        ('Описание', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Изображения', {
            'fields': ('main_image_preview', 'images_list', 'add_images'),
        }),
    )
    inlines = [ProductImageInline]

    def add_images(self, obj):
        if obj.pk:
            return format_html(
                '<a href="/admin/files/productimage/add/?product={}" class="button" style="padding: 5px 10px; background: #417690; color: white; border-radius: 4px;">'
                '➕ Добавить изображение</a>', obj.id)
        return format_html(
            '<div style="color: #999; font-style: italic;">'
            'Сохраните товар, чтобы добавить изображения'
            '</div>')
    add_images.short_description = 'Действия'

    def main_image_preview(self, obj):
        main_image = obj.product_images.filter(is_main=True).first()
        if main_image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; '
                'border: 1px solid #ddd; border-radius: 4px;"/>',
                main_image.image.url
            )
        return "Нет главного изображения"
    main_image_preview.short_description = 'Главное изображение'

    def images_list(self, obj):
        images = obj.product_images.all().order_by('-is_main')
        if images:
            return format_html(' '.join(
                f'<a href="/admin/files/productimage/{img.id}/change/" title="Редактировать">'
                f'<img src="{img.image.url}" style="max-height: 50px; margin: 5px; '
                'border: 1px solid #ddd; border-radius: 3px;"/></a>'
                for img in images
            ))
        return "Нет изображений"
    images_list.short_description = 'Все изображения'

    def images_count(self, obj):
        count = obj.product_images.count()
        return format_html(
            '<a href="/admin/files/productimage/?product__id__exact={}" style="{}">{}</a>',
            obj.id,
            'color: #417690; font-weight: bold;' if count else 'color: #999;',
            count
        )
    images_count.short_description = 'Изобр.'