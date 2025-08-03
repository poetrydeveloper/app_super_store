# analyzer.py
import os
import re
from datetime import datetime
from collections import defaultdict


def get_latest_reports():
    """Возвращает 2 последних отчета в текущей директории"""
    files = [f for f in os.listdir() if f.startswith('store_') and f.endswith('.txt')]
    return sorted(files, key=lambda x: os.path.getmtime(x))[-2:]


def parse_sections(content):
    """Разбирает содержимое на секции"""
    sections = defaultdict(list)
    current = None
    for line in content:
        line = line.strip()
        if line.startswith('## '):
            current = line[3:].strip()
        elif current:
            sections[current].append(line)
    return sections


def analyze_models(old, new):
    """Анализирует изменения в моделях"""
    report = []
    old_models = {m.split('.', 1)[1].strip(): m for m in old if re.match(r'^\d+\.', m)}
    new_models = {m.split('.', 1)[1].strip(): m for m in new if re.match(r'^\d+\.', m)}

    for name in set(new_models) - set(old_models):
        model_info = []
        for line in new[new.index(new_models[name]):]:
            if line.startswith('1.') and line != new_models[name]:
                break
            if line.strip():
                model_info.append(line.strip())
        if model_info:
            report.append(f"### Новая модель: {name}")
            report.extend(model_info)
            report.append("")
    return report


def analyze_admin(old, new):
    """Анализирует изменения в админке"""
    report = []
    old_admins = {line.split('Admin')[0].strip('- '): line for line in old if 'Admin' in line}
    new_admins = {line.split('Admin')[0].strip('- '): line for line in new if 'Admin' in line}

    for name in set(new_admins) - set(old_admins):
        admin_info = new_admins[name].strip()
        report.append(f"### Новый администратор: {name}Admin")
        report.append(admin_info)
        idx = new.index(admin_info)
        for line in new[idx + 1:]:
            if line.startswith('- ') or not line.strip():
                break
            report.append(line.strip())
        report.append("")
    return report


def generate_report(old_file, new_file):
    """Генерирует полный отчет"""
    with open(old_file, 'r', encoding='utf-8') as f:
        old_content = f.readlines()
    with open(new_file, 'r', encoding='utf-8') as f:
        new_content = f.readlines()

    old_sections = parse_sections(old_content)
    new_sections = parse_sections(new_content)

    report = [
        f"# Детальный анализ изменений",
        f"## Сравниваемые версии",
        f"- Предыдущая: {os.path.basename(old_file)}",
        f"- Текущая: {os.path.basename(new_file)}",
        f"## Дата анализа: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
        ""
    ]

    if 'Модели (кратко)' in new_sections:
        model_changes = analyze_models(
            old_sections.get('Модели (кратко)', []),
            new_sections.get('Модели (кратко)', [])
        )
        if model_changes:
            report.append("## Изменения в моделях")
            report.extend(model_changes)

    if 'Админка (основное)' in new_sections:
        admin_changes = analyze_admin(
            old_sections.get('Админка (основное)', []),
            new_sections.get('Админка (основное)', [])
        )
        if admin_changes:
            report.append("## Изменения в админке")
            report.extend(admin_changes)

    return "\n".join(report)


if __name__ == "__main__":
    try:
        old, new = get_latest_reports()
        report = generate_report(old, new)

        # Сохраняем в текущую директорию
        out_file = f"Analyze_{os.path.basename(new)}"
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(report)

    except Exception as e:
        # Логирование ошибок в файл error.log в текущей директории
        with open("analyzer_error.log", 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()}: {str(e)}\n")