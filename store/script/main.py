import os
import datetime
import sys
from pathlib import Path

# Настройка Django окружения
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'store.settings')

import django

django.setup()


def generate_project_map():
    """Генерирует карту проекта с учётом, что приложений может не быть"""
    output = []
    project_name = "store"
    # Изменён формат даты (заменяем : на - и убираем миллисекунды)
    now = datetime.datetime.now().strftime("%d-%m-%y_%H-%M-%S")  # Было "%d-%m-%y_%H:%M:%S:%f"[:-4]
    output.append(f"# Проект: {project_name} | Дата: {now}\n")

    # Проверка наличия моделей
    from django.apps import apps
    models = apps.get_models()

    if not models:
        output.append("## Модели\nВ проекте пока нет моделей")
    else:
        output.append("## Модели")
        for model in models:
            output.append(f"1. {model.__name__}")
            # ... (остальной код анализа моделей)

    # Админка
    output.append("\n## Админка")
    try:
        from django.contrib import admin
        if not admin.site._registry:
            output.append("Админка не настроена (нет зарегистрированных моделей)")
        else:
            for model, admin_class in admin.site._registry.items():
                output.append(f"- {model.__name__}Admin:")
                if admin_class.list_display:
                    output.append(f"  - list_display: {list(admin_class.list_display)}")
    except ImportError:
        output.append("Модуль admin не доступен")

    # Views (упрощённая проверка)
    output.append("\n## Views")
    output.append("Пока не анализировались (в проекте нет приложений)")

    # URLs
    output.append("\n## URLs")
    try:
        from django.urls import get_resolver
        urls = [pattern.pattern for pattern in get_resolver().url_patterns]
        if not urls:
            output.append("Нет пользовательских URL-маршрутов")
        else:
            output.extend([f"- {url}" for url in urls])
    except Exception as e:
        output.append(f"Ошибка при получении URLs: {str(e)}")

    # Сохранение
    filename = f"{project_name}_{now}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(output))
    print(f"Карта проекта сохранена в {filename}")


if __name__ == "__main__":
    generate_project_map()