import os
import re
from difflib import unified_diff
from collections import defaultdict


def find_latest_maps(prefix="store"):
    files = [f for f in os.listdir('')
             if f.startswith(prefix) and f.endswith('.txt') and not f.startswith('Analyze')]
    return sorted(files, reverse=True)[:2]


def analyze_changes(file1, file2):
    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        old = f1.readlines()
        new = f2.readlines()

    changes = defaultdict(list)
    current_section = None

    for line in unified_diff(old, new, n=3):
        if line.startswith('@@'):
            continue
        elif line.startswith('+## '):
            current_section = line[4:].strip()
        elif line.startswith('+'):
            if current_section:
                changes[current_section].append(f"Добавлено: {line[1:].strip()}")
        elif line.startswith('-'):
            if current_section:
                changes[current_section].append(f"Удалено: {line[1:].strip()}")

    # Генерация отчета
    report = [f"# Анализ изменений: {os.path.splitext(file2)[0]} vs {os.path.splitext(file1)[0]}"]

    for section, items in changes.items():
        report.append(f"\n## Изменения в {section}")
        report.extend(items[:15])  # Ограничиваем количество записей

    # Сохранение
    analyze_filename = f"Analyze_{os.path.splitext(file2)[0]}.txt"
    with open(analyze_filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    print(f"Отчет сохранен в {analyze_filename}")


if __name__ == "__main__":
    latest = find_latest_maps()
    if len(latest) == 2:
        analyze_changes(*latest)
    else:
        print("Нужно минимум 2 файла карты для сравнения")