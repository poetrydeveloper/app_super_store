import os
import datetime
import sys
import inspect
from pathlib import Path
from django.db import models

# Настройка Django окружения
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'store.settings')

import django

django.setup()


def get_model_summary(model):
    """Возвращает компактное описание модели"""
    summary = []

    # Основные поля
    fields = []
    for field in model._meta.get_fields():
        if isinstance(field, models.Field):
            field_info = f"{field.name}: {field.__class__.__name__}"
            if hasattr(field, 'max_length') and field.max_length:
                field_info += f"({field.max_length})"
            fields.append(field_info)

    summary.append("Поля: " + ", ".join(fields[:5]) + ("..." if len(fields) > 5 else ""))

    # Валидация
    if hasattr(model, 'clean'):
        summary.append("Есть метод clean()")

    # Пользовательские методы
    custom_methods = [
        name for name, _ in inspect.getmembers(model, inspect.isfunction)
        if not name.startswith('_') and not hasattr(models.Model, name)
    ]
    if custom_methods:
        summary.append(f"Методы: {', '.join(custom_methods[:3])}" +
                       ("..." if len(custom_methods) > 3 else ""))

    return "\n".join(summary)


def generate_compact_project_map():
    """Генерирует компактную карту проекта"""
    output = []
    project_name = "store"
    now = datetime.datetime.now().strftime("%d-%m-%y_%H-%M-%S")
    output.append(f"# Проект: {project_name} | Дата: {now}\n")

    # Модели
    from django.apps import apps
    output.append("## Модели (кратко)")
    for model in apps.get_models():
        output.append(f"\n1. {model.__name__}")
        output.append(get_model_summary(model))

    # Админка (только основные данные)
    output.append("\n## Админка (основное)")
    try:
        from django.contrib import admin
        for model, admin_class in admin.site._registry.items():
            output.append(f"- {model.__name__}Admin")
            if admin_class.list_display:
                output.append(f"  Отображаемые поля: {admin_class.list_display[:3]}")
    except ImportError:
        output.append("Админка не доступна")

    # Views и URLs (кратко)
    output.append("\n## Views")
    output.append("Требуется ручная проверка")

    output.append("\n## URLs")
    try:
        from django.urls import get_resolver
        urls = [pattern.pattern for pattern in get_resolver().url_patterns[:5]]
        output.extend([f"- {url}" for url in urls])
        if len(get_resolver().url_patterns) > 5:
            output.append(f"...и еще {len(get_resolver().url_patterns) - 5} URL-ов")
    except Exception:
        output.append("Не удалось получить URLs")

    # Сохранение
    filename = f"{project_name}_{now}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(output))
    print(f"Компактная карта проекта сохранена в {filename} (всего {len(output)} строк)")


if __name__ == "__main__":
    generate_compact_project_map()