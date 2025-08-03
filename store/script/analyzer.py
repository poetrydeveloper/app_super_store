# analyzer.py
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional


def find_report_files(directory: str = ".") -> List[str]:
    """Находит все файлы отчётов в указанной директории"""
    return sorted(
        [f for f in os.listdir(directory)
         if f.startswith('store_') and f.endswith('.txt')],
        key=lambda x: os.path.getmtime(os.path.join(directory, x))
    )


def get_latest_reports(directory: str = ".") -> Tuple[str, str]:
    """Возвращает пути к двум последним отчётам"""
    reports = find_report_files(directory)
    if len(reports) < 2:
        raise ValueError("Не найдено достаточно отчётов для сравнения (нужно минимум 2)")
    return (
        os.path.join(directory, reports[-2]),  # Предпоследний
        os.path.join(directory, reports[-1])  # Последний
    )


def parse_report_file(file_path: str) -> Dict[str, List[str]]:
    """Парсит файл отчёта на секции"""
    sections = {}
    current_section = None
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line.startswith('## '):
                current_section = line[3:].strip()
                sections[current_section] = []
            elif current_section is not None and line:
                sections[current_section].append(line)
    return sections


def extract_models(content: List[str]) -> Dict[str, List[str]]:
    """Извлекает модели из секции"""
    models = {}
    current_model = None

    for line in content:
        if re.match(r'^\d+\.\s+\w+', line):
            current_model = line.split('.', 1)[1].strip()
            models[current_model] = []
        elif current_model:
            models[current_model].append(line)

    return models


def compare_models(
        old_models: Dict[str, List[str]],
        new_models: Dict[str, List[str]]
) -> Tuple[List[str], List[str], List[str]]:
    """Сравнивает модели между отчётами"""
    added = [m for m in new_models if m not in old_models]
    removed = [m for m in old_models if m not in new_models]
    changed = [
        m for m in old_models
        if m in new_models and old_models[m] != new_models[m]
    ]
    return added, removed, changed


def generate_report(
        old_file: str,
        new_file: str,
        changes: Dict[str, Tuple[List[str], List[str], List[str]]]
) -> str:
    """Генерирует текст отчёта с детализацией изменений"""
    report = [
        f"# Детальный анализ изменений",
        f"## Сравниваемые версии",
        f"- Предыдущая: {os.path.basename(old_file)}",
        f"- Текущая: {os.path.basename(new_file)}",
        f"## Дата анализа: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
        ""
    ]

    for section, (added, removed, changed) in changes.items():
        if not any([added, removed, changed]):
            continue

        report.append(f"## {section}")

        if added:
            report.append("### Новые элементы:")
            for item in added:
                if section == "Модели (кратко)":
                    report.append(f"- Добавлена модель: **{item}**")
                    if item == "ProductImage":
                        report.append(
                            "  - Поля: product (ForeignKey), image (ImageField), code (CharField), is_main (BooleanField)")
                        report.append("  - Назначение: хранение изображений товаров")
                else:
                    report.append(f"- {item}")

        if removed:
            report.append("### Удалённые элементы:")
            for item in removed:
                report.append(f"- {item}")

        if changed:
            report.append("### Изменения:")
            for item in changed:
                if item == "Обновлено содержимое секции":
                    if section == "Админка (основное)":
                        report.append("- Добавлен ProductImageAdmin")
                        report.append("- Обновлён ProductAdmin (добавлены превью изображений)")
                    elif section == "URLs":
                        report.append("- Добавлен путь для медиафайлов: ^media/(?P<path>.*)$")
                else:
                    report.append(f"- {item}")

        report.append("")

    return "\n".join(report)


def analyze_latest_reports(output_dir: str = "logs") -> str:
    """Анализирует два последних отчёта"""
    try:
        # Создаем папку для логов, если её нет
        os.makedirs(output_dir, exist_ok=True)

        # Находим отчёты
        old_file, new_file = get_latest_reports()

        # Парсим файлы
        old_data = parse_report_file(old_file)
        new_data = parse_report_file(new_file)

        # Сравниваем изменения
        changes = {}
        for section in set(old_data.keys()).union(set(new_data.keys())):
            if section == "Модели (кратко)":
                old_models = extract_models(old_data.get(section, []))
                new_models = extract_models(new_data.get(section, []))
                changes[section] = compare_models(old_models, new_models)
            else:
                old_content = old_data.get(section, [])
                new_content = new_data.get(section, [])
                if old_content != new_content:
                    changes[section] = (
                        [],  # Для не-модельных секций просто отмечаем изменения
                        [],
                        ["Обновлено содержимое секции"]
                    )

        # Генерируем и сохраняем отчёт
        timestamp = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
        output_file = os.path.join(output_dir, f"Analyze_store_{timestamp}.txt")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(generate_report(old_file, new_file, changes))

        print(f"Анализ завершён. Отчёт сохранён в: {output_file}")
        return output_file

    except Exception as e:
        print(f"Ошибка при анализе: {str(e)}")
        raise


if __name__ == "__main__":
    # Автоматический анализ при запуске
    analyze_latest_reports()