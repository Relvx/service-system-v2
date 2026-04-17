# Schedule Print Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить кнопку «Распечатать месяц» в раздел Расписание — по клику открывается новая вкладка с чистой таблицей клиентов/договоров/пометок/выездов, браузер предлагает печать.

**Architecture:** Новый маршрут `/print/schedule/:year/:month` рендерит `PrintSchedulePage.vue` без Layout. При монтировании запрашивает `GET /schedule/month` и параллельно `GET /visits?contract_id=X&status=done&limit=3` для каждого договора, затем вызывает `window.print()`. Кнопка в `SchedulePage.vue` открывает этот маршрут в новой вкладке.

**Tech Stack:** Vue 3 (Composition API), Vue Router 4, axios (через `api.js`)

---

## Файлы

| Файл | Действие |
|------|----------|
| `frontend/src/pages/PrintSchedulePage.vue` | Создать |
| `frontend/src/router/index.js` | Добавить роут (строка ~101) |
| `frontend/src/pages/SchedulePage.vue` | Добавить кнопку «Распечатать месяц» |

---

## Task 1: Новый компонент PrintSchedulePage.vue

**Files:**
- Create: `frontend/src/pages/PrintSchedulePage.vue`

- [ ] **Шаг 1: Создать компонент с разметкой таблицы**

Создать `frontend/src/pages/PrintSchedulePage.vue`:

```vue
<template>
  <div class="print-page">
    <!-- Шапка -->
    <div class="print-header">
      <h1>Расписание на {{ monthName }} {{ year }}</h1>
      <p class="print-meta">Сформировано: {{ today }}</p>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="print-loading no-print">
      <p>Загрузка данных...</p>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="no-print">
      <p>Ошибка загрузки: {{ error }}</p>
    </div>

    <!-- Таблица -->
    <table v-else class="print-table">
      <thead>
        <tr>
          <th class="col-num">#</th>
          <th class="col-client">Клиент</th>
          <th class="col-contract">Договор</th>
          <th class="col-note">Пометки</th>
          <th class="col-visits">Последние выезды</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, idx) in rows" :key="row.contract_id">
          <td class="col-num">{{ idx + 1 }}</td>
          <td class="col-client">{{ row.client_name }}</td>
          <td class="col-contract">{{ row.contract_number }}</td>
          <td class="col-note">{{ row.note || '' }}</td>
          <td class="col-visits">
            <div v-if="row.visits && row.visits.length" class="visits-list">
              <div v-for="v in row.visits" :key="v.id" class="visit-item">
                <span class="visit-date">{{ formatDate(v.planned_date) }}</span>
                <span v-if="v.work_summary" class="visit-summary"> — {{ v.work_summary }}</span>
              </div>
            </div>
            <span v-else class="no-visits">—</span>
          </td>
        </tr>
        <tr v-if="rows.length === 0">
          <td colspan="5" class="empty-row">Нет договоров в этом месяце</td>
        </tr>
      </tbody>
    </table>

    <!-- Подвал -->
    <div v-if="!loading && !error" class="print-footer">
      Всего: {{ rows.length }} {{ pluralContracts(rows.length) }}
    </div>

    <!-- Кнопка закрыть (скрывается при печати) -->
    <div class="no-print close-btn-wrap">
      <button @click="window.close()">Закрыть</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { scheduleAPI, visitsAPI } from '../services/api.js'

const route = useRoute()
const year = Number(route.params.year)
const month = Number(route.params.month)

const MONTHS_FULL = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

const monthName = computed(() => MONTHS_FULL[month - 1])

const now = new Date()
const today = `${String(now.getDate()).padStart(2, '0')}.${String(now.getMonth() + 1).padStart(2, '0')}.${now.getFullYear()}`

const loading = ref(true)
const error = ref(null)
const rows = ref([])

function formatDate(dateStr) {
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-')
  return `${d}.${m}.${y}`
}

function pluralContracts(n) {
  if (n % 10 === 1 && n % 100 !== 11) return 'договор'
  if ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100)) return 'договора'
  return 'договоров'
}

onMounted(async () => {
  try {
    const schedRes = await scheduleAPI.getMonth(year, month)
    const items = schedRes.data.items

    // Параллельно запрашиваем последние 3 выезда для каждого договора
    const visitsResults = await Promise.all(
      items.map(item =>
        visitsAPI.getAll({ contract_id: item.contract_id, status: 'done', limit: 3 })
          .then(r => r.data.items || r.data)
          .catch(() => [])
      )
    )

    rows.value = items.map((item, i) => ({
      ...item,
      visits: visitsResults[i] || [],
    }))
  } catch (e) {
    error.value = e?.message || 'Неизвестная ошибка'
  } finally {
    loading.value = false
    if (!error.value) {
      // Небольшая задержка чтобы Vue успел отрендерить таблицу
      setTimeout(() => window.print(), 300)
    }
  }
})
</script>

<style>
* { box-sizing: border-box; }

body { margin: 0; font-family: Arial, sans-serif; font-size: 11pt; color: #000; }

.print-page { padding: 10mm; }

.print-header { margin-bottom: 6mm; }
.print-header h1 { font-size: 16pt; margin: 0 0 2mm 0; }
.print-meta { font-size: 9pt; color: #666; margin: 0; }

.print-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 4mm;
}
.print-table th,
.print-table td {
  border: 1px solid #999;
  padding: 2mm 3mm;
  vertical-align: top;
  text-align: left;
}
.print-table th { background: #f0f0f0; font-weight: bold; font-size: 10pt; }

.col-num      { width: 6mm; text-align: center; }
.col-client   { width: 22%; }
.col-contract { width: 18%; }
.col-note     { width: 18%; }
.col-visits   { width: auto; }

.visits-list { display: flex; flex-direction: column; gap: 1mm; }
.visit-date { font-weight: 600; }
.visit-summary { color: #333; }
.no-visits { color: #999; }
.empty-row { text-align: center; color: #999; padding: 4mm; }

.print-footer { font-size: 9pt; color: #555; margin-top: 3mm; }

.print-loading { text-align: center; padding: 20mm; color: #666; }

.close-btn-wrap { margin-top: 6mm; text-align: right; }
.close-btn-wrap button {
  padding: 6px 16px; cursor: pointer;
  border: 1px solid #ccc; border-radius: 4px;
  background: #f5f5f5; font-size: 11pt;
}

@page { size: A4 landscape; margin: 10mm; }
@media print { .no-print { display: none !important; } }
</style>
```

- [ ] **Шаг 2: Проверить в браузере**

Запустить dev-сервер (если не запущен): `cd frontend && npm run dev`

Открыть вручную: `http://localhost:5173/print/schedule/2026/4`

Убедиться:
- Таблица рендерится с данными
- Автоматически открывается диалог печати
- Кнопка «Закрыть» видна до печати, не видна в превью печати

---

## Task 2: Добавить маршрут в router/index.js

**Files:**
- Modify: `frontend/src/router/index.js:98-101`

- [ ] **Шаг 1: Добавить роут**

В файле `frontend/src/router/index.js` после строки `/schedule` добавить новый маршрут:

```js
  {
    path: '/schedule',
    component: () => import('../pages/SchedulePage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['office_group', 'admin_group'] },
  },
  // --- ДОБАВИТЬ ПОСЛЕ ---
  {
    path: '/print/schedule/:year/:month',
    component: () => import('../pages/PrintSchedulePage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['office_group', 'admin_group'] },
  },
```

- [ ] **Шаг 2: Проверить навигацию**

Открыть `http://localhost:5173/print/schedule/2026/4` — должна открыться страница печати без редиректа.

---

## Task 3: Добавить кнопку в SchedulePage.vue

**Files:**
- Modify: `frontend/src/pages/SchedulePage.vue`

- [ ] **Шаг 1: Добавить импорт иконки Printer**

В `SchedulePage.vue` найти строку с импортами Lucide (~строка 402):

```js
import {
  ChevronLeft, ChevronRight, Calendar as CalendarIcon,
  X, ExternalLink, MessageSquare, Pencil, Search, ArrowRight, AlertTriangle,
} from 'lucide-vue-next'
```

Заменить на:

```js
import {
  ChevronLeft, ChevronRight, Calendar as CalendarIcon,
  X, ExternalLink, MessageSquare, Pencil, Search, ArrowRight, AlertTriangle, Printer,
} from 'lucide-vue-next'
```

- [ ] **Шаг 2: Добавить функцию printMonth в script**

После функции `goNextMonth` (~строка 457) добавить:

```js
function printMonth() {
  const y = currentYear.value
  const m = viewMode.value === 'month' ? currentMonth.value : currentMonth.value
  window.open(`/print/schedule/${y}/${m}`, '_blank')
}
```

- [ ] **Шаг 3: Добавить кнопку в template**

В шапке страницы (`<div class="flex flex-wrap items-center gap-2">`), после кнопки «Следующий месяц» (~строка 58), добавить:

```html
          <!-- Кнопка печати -->
          <button
            @click="printMonth"
            class="btn btn-secondary text-sm flex items-center gap-1 flex-shrink-0"
            title="Распечатать расписание на месяц"
          >
            <Printer class="w-4 h-4" />
            Распечатать месяц
          </button>
```

- [ ] **Шаг 4: Проверить работу кнопки**

Открыть `http://localhost:5173/schedule`

- В режиме «Год» — клик на «Распечатать месяц» → открывается новая вкладка с текущим месяцем
- В режиме «Месяц» — клик → открывается новая вкладка с выбранным месяцем
- Таблица в новой вкладке содержит данные

- [ ] **Шаг 5: Коммит**

```bash
git add frontend/src/pages/PrintSchedulePage.vue \
        frontend/src/router/index.js \
        frontend/src/pages/SchedulePage.vue
git commit -m "feat: печать расписания на месяц — новая вкладка с таблицей"
```

---

## Self-Review

**Spec coverage:**
- ✅ Кнопка доступна в обоих режимах (год и месяц)
- ✅ Новая вкладка с чистой страницей (без Layout)
- ✅ Столбцы: #, Клиент, Договор, Пометки, Последние выезды
- ✅ До 3 последних выездов: дата + work_summary
- ✅ auto `window.print()` после загрузки данных
- ✅ Альбомная ориентация A4
- ✅ Кнопка «Закрыть» скрыта при печати

**Placeholder scan:** нет TBD/TODO

**Type consistency:** `scheduleAPI.getMonth` → `.data.items`, `visitsAPI.getAll` → `.data.items || .data` (защита на оба варианта ответа)
