# Changelog

Все заметные изменения в проекте будут документироваться в этом файле.  
Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/).

---

## [Unreleased]  
*Последние изменения в разработке.*

### Added  
- Добавлены административные классы для управления моделями через админку:  
  - **CategoryAdmin** с отображаемыми полями: `name`, `parent_link`, `slug_display`  
  - **ProductAdmin** с отображаемыми полями: `name`, `code`, `category`  

### Changed  
- *Нет изменений в существующем функционале*  

### Fixed  
- *Нет исправлений багов*  

---

## [0.1.0] - 2025-08-02  
*Первая задокументированная версия проекта.*

### Added  
- Базовые модели Django:  
  - `User`, `Group`, `Permission`, `Session`, `ContentType`, `LogEntry`  
- Кастомные модели:  
  - **Category**: Поля `name`, `slug`, `parent` (ForeignKey)  
  - **Product**: Поля `code`, `name`, `description`, `category` (ForeignKey)  
- Начальная настройка админ-панели для:  
  - `UserAdmin` (поля: `username`, `email`, `first_name`)  
  - `GroupAdmin` (поля: `__str__`)  
- Корневой URL `/admin/`  

### Infrastructure  
- Скрипт для создания "слепков" проекта и анализа изменений  

---

### Правила ведения журнала:  
1. **"Added"** — для новой функциональности.  
2. **"Changed"** — для изменений в существующем коде.  
3. **"Fixed"** — для исправлений багов.  
4. **Дата** в формате `YYYY-MM-DD`.  
5. **Версии** — по схеме `v0.1.0` (SemVer).  
