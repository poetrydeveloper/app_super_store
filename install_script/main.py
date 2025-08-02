import os
import datetime
from django.apps import apps
from django.conf import settings
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'store.settings')  # Было 'your_project.settings'
import django

django.setup()


def get_model_details(model):
    """Возвращает детализированное описание модели"""
    details = []
    for field in model._meta.fields + model._meta.many_to_many:
        field_info = {
            'name': field.name,
            'type': field.__class__.__name__,
            'params': []
        }

        # Стандартные параметры
        if field.verbose_name: field_info['verbose_name'] = field.verbose_name
        if field.help_text: field_info['help_text'] = field.help_text
        if field.max_length: field_info['params'].append(f"max_length={field.max_length}")
        if field.null: field_info['params'].append("null=True")
        if field.blank: field_info['params'].append("blank=True")
        if field.default: field_info['params'].append(f"default={field.default}")

        # Для связей
        if hasattr(field, 'related_model'):
            field_info['params'].append(f"to={field.related_model.__name__}")
            if hasattr(field, 'on_delete'):
                field_info['params'].append(f"on_delete={field.on_delete.__name__}")
            if field.remote_field.related_name:
                field_info['params'].append(f"related_name='{field.remote_field.related_name}'")

        # Форматируем строку
        param_str = ", ".join(field_info['params'])
        details.append(f"   - {field.name}: {field_info['type']}({param_str})")
        if 'verbose_name' in field_info:
            details.append(f"     # verbose_name: '{field_info['verbose_name']}'")

    return details


def get_views_info():
    """Анализирует views.py и возвращает информацию о методах"""
    views_info = []
    for app in apps.get_app_configs():
        try:
            views_module = __import__(f"{app.name}.views", fromlist=[''])
            for name, obj in vars(views_module).items():
                if hasattr(obj, '__module__') and obj.__module__.startswith(app.name):
                    if hasattr(obj, 'http_method_names'):
                        methods = [m.upper() for m in obj.http_method_names if m.upper() in ('GET', 'POST')]
                        views_info.append(f"- {name}: {', '.join(methods)}")
                    elif callable(obj):
                        views_info.append(f"- {name}: FUNCTION")
        except ImportError:
            continue
    return views_info


def get_templates_info():
    """Сканирует шаблоны в директориях templates"""
    templates = []
    for app in apps.get_app_configs():
        template_dir = Path(app.path) / 'templates'
        if template_dir.exists():
            for file in template_dir.rglob('*.html'):
                rel_path = str(file.relative_to(template_dir))
                templates.append(f"- {app.name}/{rel_path}")
    return templates


def generate_project_map():
    """Генерирует полную карту проекта"""
    output = []
    project_name = "store"
    now = datetime.datetime.now().strftime("%d-%m-%y_%H:%M:%S:%f")[:-4]
    output.append(f"# Проект: {project_name} | Дата: {now}\n")

    # Модели с детализацией
    output.append("## Модели")
    for model in apps.get_models():
        output.append(f"1. {model.__name__}")
        output.extend(get_model_details(model))
        output.append("")

    # Админка
    output.append("## Админка")
    try:
        from django.contrib import admin
        for model, admin_class in admin.site._registry.items():
            output.append(f"- {model.__name__}Admin:")
            if admin_class.list_display:
                output.append(f"  - list_display: {list(admin_class.list_display)}")
            if admin_class.search_fields:
                output.append(f"  - search_fields: {admin_class.search_fields}")
    except ImportError:
        output.append("Админка не настроена")

    # Views с методами
    output.append("\n## Views")
    output.extend(get_views_info() or ["Нет views"])

    # URLs
    output.append("\n## URLs")
    try:
        from django.urls import get_resolver
        for url in get_resolver().url_patterns:
            if hasattr(url, 'pattern'):
                output.append(f"- {url.pattern}")
    except Exception:
        output.append("Не удалось получить URLs")

    # Шаблоны
    output.append("\n## Templates")
    templates = get_templates_info()
    output.extend(templates if templates else ["Нет шаблонов"])

    # Сохранение
    filename = f"{project_name}_{now}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(output))
    print(f"Карта сохранена в {filename}")


if __name__ == "__main__":
    generate_project_map()