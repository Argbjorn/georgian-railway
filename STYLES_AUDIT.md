# Аудит стилей (временный)

Файл временный: удалить, когда пункты будут разобраны. Аудит сделан по коду, без сборки сайта; пометка «проверить» — вывод только по коду.

Файлы стилей:
- `assets/css/custom.css` — все страницы (через пайплайн Hugo);
- `static/css/sidebar.css` — панель на главной (подключается в `layouts/partials/map.html`);
- инлайн: `<style>` в `layouts/_default/whats-new-list.html`, `layouts/partials/esd_calendar.html`, `layouts/partials/custom/head-end.html`; `style="…"` в шаблонах `layouts/_default/*`, `404.html`, `footer.html`.

## 1. Главная и остальные страницы — две разные системы

Панель на главной (`sidebar.css`) написана отдельно, со своей палитрой и компонентами; остальные страницы остались на старых стилях `custom.css`.

### Синий акцент — пять оттенков
| Цвет | Где |
|---|---|
| `#1B6EA8` | панель на главной, мобильное меню (`.mobile-menu-link.is-active`) |
| `hsl(212 100% 45%)` | `--link-color`: все ссылки (`custom.css:3`), рамка миниатюры галереи |
| `#0078A8` | `.station-route-ref`, подчёркивание `.station-route-name` / `.station-name`, `.route-link.active` |
| `#3A8BC4` | рамка `.train-number-badge` в панели |
| `#3b82f6` | кнопка на 404 (инлайн) |

### Зелёный линии маршрута — четыре варианта
- `#22A022` — `.route-stops` в панели;
- `#199900` — `.route-timeline` и `.route-schedule-table` на странице маршрута, `.map-expand-button`;
- `#137000` — наведение на `.map-expand-button`;
- `#f0f9f0` / `#2d5a2d` — дни поезда в календаре (`esd_calendar.html`).

### Серые — три набора
- палитра панели: `#15181C`, `#2A3036`, `#4A525B`, `#5B636D`, `#D5D9DE`, `#E3E6EA`, `#F2F4F6`;
- Tailwind: `#e5e7eb`, `#6b7280`, `#9ca3af`, `#1f2937`, `#f8fafc`, `#f1f5f9`, `#334155`;
- разрозненные: `#333`, `#eee`, `#e0e0e0` (футер), `#666`, `#838383`.

### Одинаковые сущности с разным видом
- **Бейдж номера поезда — три варианта:**
  - `.train-number-badge` (`sidebar.css:309`) — панель: синий, радиус 4px;
  - `.station-route-ref` (`custom.css:388`) — страница станции: другой синий, радиус 3px, `min-width: 53px`;
  - `.link-list-badge` (`custom.css:105`) — список маршрутов: серый.
- **Список остановок — два варианта:**
  - `.route-stops` (`sidebar.css:390`) — flex, кружок 12px, обводка 2.5px;
  - `.route-timeline` (`custom.css:270-316`) — абсолютное позиционирование, кружок 16px, обводка 2px. Линия держится на подогнанных числах (`top: 15px; bottom: 25px; left: 4.45rem`) и съедет при смене шрифта или высоты строки.
- **Поезда на станции — два варианта:**
  - `.station-train` в панели — время 48px, 700, `tabular-nums`;
  - `.station-route` на странице станции — время 45px, `font-family: 'Roboto Mono'` (`custom.css:416`). Шрифт не подключён, браузер берёт системный моноширинный.
- **Заголовки разделов:** панель — 18px/700; список маршрутов — `hx:text-xl` (20px)/600; страница станции — 1.5rem, `#333`.

### Шрифт карты
`#map` задаёт `font-family: "Roboto"` (`custom.css:228`), шрифт не подключён. Подсказки с названиями станций на главной идут запасным `sans-serif` (на Windows — Arial). Карты на страницах станций и маршрутов (`.route-map-container`) наследуют шрифт сайта.

### Единицы
Панель — px, остальное — rem/em вперемешку.

## 2. Похоже на ошибки

1. ~~`nav > a, li > a`~~ — не ошибка: ссылки в списках выглядят корректно.
2. ~~`body, html { overflow-x: hidden }` ломает sticky-шапку~~ — шапка не прилипает, так и оставлено.
3. [x] **Позиционирование `#map`**: вместо `100vw` + отрицательных отступов + `left: 50%`/`30%` — `position: fixed; inset: var(--navbar-height) 0 0`.
4. [x] **Высота шапки `64px` числом** в `#map` и `.sidebar` → `var(--navbar-height)` (Hextra, 4rem).
5. [x] **Граница 768px**: `.route-schedule-table` переведена на `max-width: 767px`, как у панели.

## 3. Мёртвый код

- [x] `static/css/leaflet-beautify-marker-icon.css` и `static/js/leaflet-beautify-marker-icon.js` — остатки Leaflet, нигде не подключены.
- [x] `@keyframes sweep` (`custom.css:265`) и `@keyframes fade-in` (`custom.css:724`) — не используются.
- [x] `.route-link.active` (`custom.css:260`) — класс `active` на `.route-link` никто не ставит.
- [x] `.station-icon.active` (`custom.css:797`) — `active` ставится на маркер, не на значок; работает `.station-marker.active .station-icon`.
- [x] `.fullscreen-close-button:hover` записано дважды (`custom.css:1012` и `1023`).
- [x] `.station-route:hover { background-color: transparent }` и `border-left: 1px dotted transparent` у `.station-route` — ничего не делают.
- [x] `--link-hover-color` равен `--link-color`.
- [x] Все правила `.dark …` (`.link-list`, `.mobile-menu-link`, `.tg-caption`, заглушка обложки поезда): в `hugo.yaml` `theme.displayToggle: false`, `theme.default: light` — тёмная тема не включается. В панели тёмной темы нет, таблица расписания жёстко ставит `#fff !important`. Удалены.
- [x] Стили крестика попапа MapLibre (~50 строк с `!important`, `custom.css:819-869`): единственный попап (`BaseStation.js`) создаётся с `closeButton: false`.

## 4. Структура

- Обёртка `<div class="content-max-width" style="display: flex;">` + `<div style="min-width: 0; flex: 1; padding: 2rem 1.5rem;">` повторяется инлайном в шести шаблонах (`routes-list`, `stations-list`, `stations-single`, `trains-list`, `whats-new-list`, `404`) — сделать классом.
- Кнопка на 404 и рамка в `layouts/partials/footer.html:20` — инлайн-стили со своими цветами (`#3b82f6`, `#e0e0e0`).
- Стили «Что нового» — блоком `<style>` в `whats-new-list.html`, а не в `custom.css`.
- Два способа запретить прокрутку: галерея — `html.tg-lock`; полноэкранная карта — `body.fullscreen-open` с `position: fixed` и `!important`.
- `z-index` не согласован: галерея 1000, затемнение карты 1000/1001, полноэкранная карта 9999/10000, `#map` и панель — 10.
- `.route-map-container` стоит и на внешнем, и на внутреннем `div` (`route-map.html:1-2`, `station-map.html:5-6`) — высота и `margin-top` применяются дважды.
- `.maplibregl-popup { max-width: 350px !important }` — можно задать опцией `maxWidth` при создании попапа.

## План

1. [x] Удалить мёртвый код (раздел 3).
2. [x] Исправить ошибки из раздела 2.
3. [ ] Завести общие CSS-переменные в `:root` в `custom.css` (грузится и на главной): акцент, зелёный линии, текст, вторичный текст, рамки, фон при наведении. Перевести на них `sidebar.css` и остальные страницы. Предложение — взять палитру панели: синий `#1B6EA8`, зелёный `#22A022`.
4. [ ] Свести к одному виду: бейдж номера поезда, список остановок, строку поезда на станции.
5. [ ] Убрать инлайн-стили и `<style>`-блоки в `custom.css` (кроме `esd_calendar.html` — там намеренно, см. `CLAUDE.md`).
