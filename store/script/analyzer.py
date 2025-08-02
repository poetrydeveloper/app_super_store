import os
from pathlib import Path
from difflib import unified_diff
from collections import defaultdict


def find_latest_maps(prefix="store"):
    """Находит 2 последних файла карты в директории скрипта"""
    script_dir = Path(__file__).parent
    try:
        files = [
            f for f in os.listdir(script_dir)
            if f.startswith(prefix)
               and f.endswith('.txt')
               and not f.startswith('Analyze')
        ]
        # Сортируем по времени создания (новые сначала)
        files_with_mtime = [
            (f, os.path.getmtime(script_dir / f))
            for f in files
        ]
        files_sorted = sorted(files_with_mtime, key=lambda x: x[1], reverse=True)
        return [f[0] for f in files_sorted[:2]]
    except FileNotFoundError:
        print(f"Директория {script_dir} не найдена")
        return []
    except Exception as e:
        print(f"Ошибка при поиске файлов: {e}")
        return []


def analyze_changes(file1, file2):
    """Сравнивает два файла карты и генерирует отчет"""
    script_dir = Path(__file__).parent
    file1_path = script_dir / file1
    file2_path = script_dir / file2

    try:
        with open(file1_path, 'r', encoding='utf-8') as f1, \
                open(file2_path, 'r', encoding='utf-8') as f2:
            old = f1.readlines()
            new = f2.readlines()
    except FileNotFoundError as e:
        print(f"Ошибка при открытии файлов: {e}")
        return

    changes = defaultdict(list)
    current_section = None

    for line in unified_diff(old, new, n=3):
        line = line.strip('\n')
        if line.startswith('@@'):
            continue
        elif line.startswith('+## '):
            current_section = line[4:].strip()
        elif line.startswith('+') and not line.startswith('+++ '):
            if current_section:
                changes[current_section].append(f"[+] {line[1:]}")
        elif line.startswith('-') and not line.startswith('--- '):
            if current_section:
                changes[current_section].append(f"[-] {line[1:]}")

    # Генерация отчета
    report = [
        f"# Анализ изменений",
        f"## Сравнение: {file2} (новый) vs {file1} (старый)",
        f"Дата анализа: {os.path.getmtime(file2_path):%Y-%m-%d %H:%M:%S}"
    ]

    for section, items in changes.items():
        report.append(f"\n### Изменения в разделе: {section}")
        report.extend(items)

    # Сохранение
    analyze_filename = f"Analyze_{Path(file2).stem}.txt"
    try:
        with open(script_dir / analyze_filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        print(f"Отчет сохранен в {analyze_filename}")
    except IOError as e:
        print(f"Ошибка при сохранении отчета: {e}")


if __name__ == "__main__":
    print("Запуск анализатора изменений...")
    latest_files = find_latest_maps()

    if len(latest_files) < 2:
        print("\nОшибка: для анализа нужно минимум 2 файла карты.")
        print("Сначала создайте несколько карт через main.py")
        if latest_files:
            print("\nНайдены следующие файлы карты:")
            for f in latest_files:
                print(f"- {f}")
        else:
            print("Файлы карты не найдены.")
    else:
        print(f"\nНайдены файлы для сравнения:")
        print(f"1. {latest_files[0]} (новый)")
        print(f"2. {latest_files[1]} (старый)")
        analyze_changes(latest_files[1], latest_files[0])