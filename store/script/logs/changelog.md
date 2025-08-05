# Changelog

Все заметные изменения в проекте будут документироваться в этом файле.  
Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/).

---

## [Unreleased]  
*Последние изменения в разработке.*

### Added  
- **Новые модели для управления заявками:**
  - `Request`:
    - Поля: `created_at`, `is_completed`, `notes`
    - Методы: `get_next_by_created_at`, `get_previous_by_created_at`
  - `RequestItem`:
    - Поля: `request` (ForeignKey), `product` (ForeignKey), `quantity`, `price_per_unit`
    - Валидация через `clean()`
- **Административный интерфейс `RequestAdmin`:**
  - Отображаемые поля: `id`, `created_at`, `total_products`
  - Поддержка отображения связанных товаров в заявке

### Changed  
- **Оптимизация структуры проекта:**
  - Добавлены связи между `Request` и `Product` через `RequestItem`
  - Обновлены методы валидации для согласованности данных
- **Документация:**
  - Добавлено описание workflow заявок в README

### Fixed  
- Исправлены ошибки импортов в админ-панели (`RequestAdmin`)
- Устранены предупреждения о несуществующих полях в `list_display`

---

## [1.1.0] - 2025-08-03  
### Добавлено
- Новое приложение `files` с моделью `ProductImage`:
  - Поля: `product` (ForeignKey), `image` (ImageField), `code` (CharField), `is_main` (BooleanField)
  - Автоматическая генерация кода изображения на основе кода товара
- Административный интерфейс для изображений:
  - **ProductImageAdmin** с отображаемыми полями: `product_link`, `image_preview`, `code`
  - Превью изображений в админке
  - Фильтрация по товарам и категориям

### Changed  
- Обновлен **ProductAdmin**:
  - Добавлены разделы для работы с изображениями
  - Реализованы превью изображений
  - Добавлена кнопка быстрого добавления изображений

---

## [1.0.0] - 2025-08-02  
*Первая стабильная версия проекта.*

### Added  
- Базовые модели Django:  
  - `User`, `Group`, `Permission`, `Session`, `ContentType`, `LogEntry`  
- Кастомные модели:  
  - **Category**: Поля `name`, `slug`, `parent` (ForeignKey)  
  - **Product**: Поля `code`, `name`, `description`, `category` (ForeignKey)  

### Infrastructure  
- Скрипт для создания "слепков" проекта и анализа изменений  

---

### Правила ведения журнала:  
1. **"Added"** — для новой функциональности.  
2. **"Changed"** — для изменений в существующем коде.  
3. **"Fixed"** — для исправлений багов.  
4. **Дата** в формате `YYYY-MM-DD`.  
5. **Версии** — по схеме `v0.1.0` (SemVer).