import difflib
import os
from datetime import datetime
from typing import Dict, List, Optional

def parse_report_file(file_path: str) -> Dict[str, List[str]]:
    """Парсит файл отчёта и разбивает его на секции."""
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

def compare_sections(
    section_name: str,
    old_content: List[str],
    new_content: List[str],
) -> Optional[List[str]]:
    """Сравнивает секции и возвращает список изменений."""
    if old_content == new_content:
        return None

    diff = list(difflib.ndiff(old_content, new_content))
    changes = [f"Изменения в '{section_name}':"]
    for line in diff:
        if line.startswith('- '):
            changes.append(f"Удалено: {line[2:]}")
        elif line.startswith('+ '):
            changes.append(f"Добавлено: {line[2:]}")
    return changes

def analyze_reports(old_file: str, new_file: str, output_dir: str = ".") -> str:
    """Анализирует два файла и сохраняет отчёт."""
    old_sections = parse_report_file(old_file)
    new_sections = parse_report_file(new_file)

    report = []
    all_sections = set(old_sections.keys()).union(set(new_sections.keys()))

    changes_found = False
    for section in sorted(all_sections):
        old_data = old_sections.get(section, [])
        new_data = new_sections.get(section, [])

        diff = compare_sections(section, old_data, new_data)
        if diff:
            report.extend(diff)
            report.append("")  # Пустая строка для разделения
            changes_found = True

    if not changes_found:
        report.append("Нет изменений в моделях")

    # Добавляем примечание
    report.append("\nПримечание: Анализ выполнен улучшенным анализатором")

    # Формируем имя файла отчёта
    timestamp = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
    output_file = os.path.join(output_dir, f"Analyze_store_{timestamp}.txt")

    # Сохраняем отчёт
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Анализ изменений между {os.path.basename(new_file)} и {os.path.basename(old_file)}\n\n")
        f.write("\n".join(report))

    return output_file

if __name__ == "__main__":
    old_report = "store_02-08-25_14-32-32.txt"
    new_report = "store_02-08-25_14-37-02.txt"
    result_file = analyze_reports(old_report, new_report)
    print(f"Отчёт сохранён в файл: {result_file}")