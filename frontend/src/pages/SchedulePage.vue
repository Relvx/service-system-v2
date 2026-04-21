<template>
  <Layout>
    <div>
      <!-- Заголовок -->
      <div class="flex items-center justify-between flex-wrap gap-y-3 mb-4">
        <div>
          <h1 class="text-xl md:text-3xl font-bold text-gray-900">Расписание</h1>
          <p class="text-gray-600 mt-1">
            <span v-if="viewMode === 'year'">{{ filteredRows.length }} договоров в {{ currentYear }} году</span>
            <span v-else>{{ filteredMonthItems.length }} договоров в {{ MONTHS_FULL[currentMonth - 1] }} {{ currentYear }}</span>
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <!-- Переключатель вида -->
          <div class="flex rounded-lg border border-gray-200 overflow-hidden flex-shrink-0">
            <button
              @click="setMode('year')"
              :class="viewMode === 'year' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
              class="px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap"
            >Год</button>
            <button
              @click="setMode('month')"
              :class="viewMode === 'month' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
              class="px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap"
            >Месяц</button>
          </div>

          <!-- Навигация по году -->
          <div class="flex items-center border border-gray-200 rounded-lg overflow-hidden flex-shrink-0">
            <button @click="currentYear--; load()" class="px-2 py-2 hover:bg-gray-100 transition-colors">
              <ChevronLeft class="w-4 h-4" />
            </button>
            <span class="px-3 py-2 text-sm font-semibold w-[52px] text-center">{{ currentYear }}</span>
            <button @click="currentYear++; load()" class="px-2 py-2 hover:bg-gray-100 transition-colors">
              <ChevronRight class="w-4 h-4" />
            </button>
          </div>

          <!-- Выбор месяца (только в режиме "месяц") -->
          <select
            v-if="viewMode === 'month'"
            v-model="currentMonth"
            @change="load"
            class="input text-sm w-[140px] flex-shrink-0"
          >
            <option v-for="(m, i) in MONTHS_FULL" :key="i" :value="i + 1">{{ m }}</option>
          </select>

          <!-- Кнопка "Следующий месяц" -->
          <button
            v-if="viewMode === 'year'"
            @click="goNextMonth"
            class="btn btn-secondary text-sm flex items-center gap-1 flex-shrink-0"
          >
            <CalendarIcon class="w-4 h-4" />
            Следующий месяц
          </button>

          <!-- Кнопка печати -->
          <button
            @click="printMonth"
            class="btn btn-secondary text-sm flex items-center gap-1 flex-shrink-0"
            title="Распечатать расписание на месяц"
          >
            <Printer class="w-4 h-4" />
            Распечатать месяц
          </button>
        </div>
      </div>

      <!-- Поиск по клиенту -->
      <div class="relative mb-4 max-w-sm">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none" />
        <input
          v-model="search"
          placeholder="Поиск по клиенту или договору..."
          class="input pl-9 text-sm w-full"
        />
        <button v-if="search" @click="search = ''" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Загрузка -->
      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
      </div>

      <template v-else>

        <!-- ======= РЕЖИМ: ГОД (матрица) ======= -->
        <div v-if="viewMode === 'year'" class="card p-0 overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm border-collapse">
              <thead>
                <tr class="bg-gray-50 border-b border-gray-200">
                  <th class="text-left px-3 py-2 font-medium text-gray-600 sticky left-0 bg-gray-50 z-10 min-w-[220px] border-r border-gray-200">
                    Клиент / Договор
                  </th>
                  <th
                    v-for="(m, i) in MONTHS_SHORT"
                    :key="i"
                    class="px-2 py-2 font-medium text-gray-600 text-center min-w-[90px] whitespace-nowrap"
                    :class="isCurrentMonth(i + 1) ? 'bg-primary-50 text-primary-700' : ''"
                  >
                    {{ m }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in filteredRows"
                  :key="row.contract_id"
                  class="border-b border-gray-100 hover:bg-gray-50"
                >
                  <!-- Клиент / договор (sticky) — клик открывает карточку клиента -->
                  <td
                    class="px-3 py-2 sticky left-0 bg-white z-10 border-r border-gray-200 cursor-pointer hover:bg-blue-50 transition-colors"
                    style="max-width:260px;"
                    @click="openClientModal(row)"
                  >
                    <div class="font-medium text-gray-900 truncate text-xs">{{ row.client_name }}</div>
                    <div class="text-gray-400 truncate text-xs">{{ row.contract_number }}</div>
                  </td>
                  <!-- Ячейки месяцев -->
                  <td
                    v-for="(m, i) in MONTHS_SHORT"
                    :key="i"
                    class="px-1 py-1 text-center align-middle"
                    :class="isCurrentMonth(i + 1) ? 'bg-primary-50/40' : ''"
                  >
                    <span
                      v-if="row.cells[i + 1]"
                      class="inline-block px-2 py-1 rounded text-xs font-medium cursor-pointer
                             bg-green-100 text-green-800 hover:bg-green-200 transition-colors
                             max-w-[84px] truncate leading-tight"
                      :title="row.cells[i + 1]"
                      @click="openCellModal(row, i + 1, row.cells[i + 1])"
                    >{{ row.cells[i + 1] }}</span>
                    <button
                      v-else-if="canEdit"
                      @click="openEditModal(row, i + 1, '')"
                      class="w-full h-7 text-gray-200 hover:text-gray-400 hover:bg-gray-100 rounded transition-colors text-xs"
                    >+</button>
                  </td>
                </tr>
                <tr v-if="filteredRows.length === 0">
                  <td :colspan="13" class="text-center py-10 text-gray-400">
                    {{ search ? 'Ничего не найдено' : `Нет данных за ${currentYear} год` }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ======= РЕЖИМ: МЕСЯЦ (таблица) ======= -->
        <div v-else>
          <div v-if="filteredMonthItems.length === 0" class="card text-center py-12 text-gray-400">
            {{ search ? 'Ничего не найдено' : `Нет записей в ${MONTHS_FULL[currentMonth - 1]} ${currentYear}` }}
          </div>
          <div v-else class="card p-0 overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full text-sm border-collapse" style="table-layout: fixed;">
                <thead>
                  <tr class="bg-gray-50 border-b border-gray-200">
                    <th
                      class="text-left px-3 py-2 font-medium text-gray-600 relative select-none"
                      :style="`width: ${monthColWidth}px; min-width: 120px;`"
                    >
                      Клиент / Договор
                      <div
                        class="absolute right-0 top-0 h-full w-2 cursor-col-resize flex items-center justify-center group"
                        @mousedown.prevent="startMonthColResize"
                      >
                        <div class="w-0.5 h-4 bg-gray-300 group-hover:bg-primary-400 transition-colors rounded-full" />
                      </div>
                    </th>
                    <th class="text-left px-3 py-2 font-medium text-gray-600">Пометки</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="item in filteredMonthItems"
                    :key="item.contract_id"
                    class="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td
                      class="px-3 py-2.5 cursor-pointer align-top"
                      :style="`width: ${monthColWidth}px; min-width: 120px; word-break: break-word;`"
                      @click="openClientModal(item)"
                    >
                      <div class="font-medium text-gray-900 hover:text-primary-600 transition-colors">{{ item.client_name }}</div>
                      <div class="text-sm text-gray-400">{{ item.contract_number }}</div>
                    </td>
                    <td class="px-3 py-2.5 align-top">
                      <span
                        class="inline-block px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 cursor-pointer hover:bg-green-200 transition-colors"
                        @click="openCellModal(item, currentMonth, item.note)"
                      >{{ item.note }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </template>
    </div>

    <!-- ===== Модалка: карточка клиента ===== -->
    <div v-if="clientModal.open" class="fixed inset-0 z-50 flex items-center justify-center p-4" @keydown.esc="clientModal.open = false">
      <div class="absolute inset-0 bg-black/40" @click="clientModal.open = false" />
      <div class="relative bg-white rounded-xl shadow-xl w-full max-w-lg z-10 overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 class="text-lg font-semibold text-gray-900 truncate pr-4">{{ clientModal.clientName }}</h3>
          <button @click="clientModal.open = false" class="text-gray-400 hover:text-gray-600 flex-shrink-0">
            <X class="w-5 h-5" />
          </button>
        </div>
        <div class="px-6 py-4 space-y-3">
          <div>
            <p class="text-xs text-gray-400 mb-0.5">Договор</p>
            <p class="text-sm text-gray-800 font-medium">{{ clientModal.contractNumber }}</p>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-gray-100 flex justify-between gap-2">
          <button @click="openVisitsModal(clientModal)" class="btn btn-secondary text-sm flex items-center gap-1">
            <MessageSquare class="w-4 h-4" />
            Комментарии мастеров
          </button>
          <RouterLink
            :to="`/clients/${clientModal.clientId}`"
            @click="clientModal.open = false"
            class="btn btn-primary text-sm flex items-center gap-1"
          >
            Открыть клиента
            <ExternalLink class="w-4 h-4" />
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- ===== Модалка: ячейка расписания (просмотр + редактирование) ===== -->
    <div v-if="cellModal.open" class="fixed inset-0 z-50 flex items-center justify-center p-4" @keydown.esc="cellModal.open = false">
      <div class="absolute inset-0 bg-black/40" @click="cellModal.open = false" />
      <div class="relative bg-white rounded-xl shadow-xl w-full max-w-md z-10">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h3 class="text-base font-semibold text-gray-900">{{ cellModal.clientName }}</h3>
            <p class="text-xs text-gray-400 mt-0.5">{{ MONTHS_FULL[cellModal.month - 1] }} {{ currentYear }}</p>
          </div>
          <button @click="cellModal.open = false" class="text-gray-400 hover:text-gray-600">
            <X class="w-5 h-5" />
          </button>
        </div>
        <div class="px-6 py-4">
          <!-- Текущая заметка -->
          <div class="mb-4 px-3 py-2 bg-green-50 rounded-lg border border-green-100">
            <p class="text-xs text-green-600 font-medium mb-0.5">Расписание</p>
            <p class="text-sm text-green-900">{{ cellModal.note }}</p>
          </div>

          <!-- Кнопки действий -->
          <div class="flex gap-2">
            <button
              @click="openEditFromCell"
              v-if="canEdit"
              class="btn btn-secondary text-sm flex-1 flex items-center justify-center gap-1"
            >
              <Pencil class="w-4 h-4" />
              Изменить
            </button>
            <button
              @click="openVisitsModal(cellModal)"
              class="btn btn-secondary text-sm flex-1 flex items-center justify-center gap-1"
            >
              <MessageSquare class="w-4 h-4" />
              Комментарии
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== Модалка: редактирование ячейки ===== -->
    <div v-if="editModal.open" class="fixed inset-0 z-[60] flex items-center justify-center p-4" @keydown.esc="editModal.open = false">
      <div class="absolute inset-0 bg-black/40" @click="editModal.open = false" />
      <div class="relative bg-white rounded-xl shadow-xl p-6 w-full max-w-md z-10">
        <h3 class="text-lg font-semibold mb-1">Ячейка расписания</h3>
        <p class="text-sm text-gray-500 mb-1">{{ editModal.clientName }}</p>
        <p class="text-xs text-gray-400 mb-4">{{ editModal.contractNumber }} — {{ MONTHS_FULL[editModal.month - 1] }} {{ currentYear }}</p>

        <label class="block text-sm font-medium text-gray-700 mb-1">Заметка</label>
        <textarea
          v-model="editModal.note"
          rows="3"
          class="input w-full resize-none"
          placeholder="ТО+доки через ЭДО, пролонг..."
        />

        <div class="flex justify-between gap-2 mt-4">
          <button
            v-if="editModal.originalNote"
            @click="deleteCell"
            class="btn text-red-600 border border-red-200 hover:bg-red-50 text-sm"
          >
            Удалить
          </button>
          <div class="flex gap-2 ml-auto">
            <button @click="editModal.open = false" class="btn btn-secondary text-sm">Отмена</button>
            <button @click="saveCell" class="btn btn-primary text-sm">Сохранить</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== Модалка: комментарии мастеров ===== -->
    <div v-if="visitsModal.open" class="fixed inset-0 z-[70] flex items-center justify-center p-4" @keydown.esc="visitsModal.open = false">
      <div class="absolute inset-0 bg-black/40" @click="visitsModal.open = false" />
      <div class="relative bg-white rounded-xl shadow-xl w-full max-w-2xl z-10 flex flex-col max-h-[85vh]">

        <!-- Шапка -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 flex-shrink-0">
          <div>
            <h3 class="text-base font-semibold text-gray-900">Последние итоги выездов</h3>
            <p class="text-xs text-gray-400 mt-0.5">{{ visitsModal.clientName }} · {{ visitsModal.contractNumber }}</p>
          </div>
          <button @click="visitsModal.open = false" class="text-gray-400 hover:text-gray-600">
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Контент -->
        <div class="overflow-y-auto flex-1 px-6 py-4">
          <div v-if="visitsModal.loading" class="flex justify-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>

          <div v-else-if="visitsModal.visits.length === 0" class="text-center py-10">
            <MessageSquare class="w-10 h-10 text-gray-300 mx-auto mb-2" />
            <p class="text-gray-400 text-sm">Нет завершённых выездов с комментариями мастера</p>
            <p v-if="visitsModal.total > 0" class="text-xs text-gray-400 mt-1">
              Всего выездов по договору: {{ visitsModal.total }}
            </p>
          </div>

          <div v-else class="space-y-4">
            <!-- Подзаголовок с кол-вом -->
            <p class="text-xs text-gray-400">
              Показаны последние {{ visitsModal.visits.length }} из {{ visitsModal.total }} завершённых выездов
            </p>

            <div
              v-for="v in visitsModal.visits"
              :key="v.id"
              class="border border-gray-100 rounded-xl p-4 space-y-3"
            >
              <!-- Шапка записи -->
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <p class="text-sm font-medium text-gray-800 truncate">{{ v.site_title || '—' }}</p>
                  <div class="flex items-center gap-3 mt-0.5 flex-wrap">
                    <span class="text-xs text-gray-500">{{ formatDate(v.planned_date) }}</span>
                    <span v-if="v.master_names && v.master_names.length" class="text-xs text-gray-400">
                      {{ v.master_names.join(', ') }}
                    </span>
                    <span v-else-if="v.master_name" class="text-xs text-gray-400">{{ v.master_name }}</span>
                    <span v-if="v.visit_type" class="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
                      {{ cfg.visitTypeLabel(v.visit_type) }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Итог работ -->
              <div v-if="v.work_summary">
                <p class="text-xs text-gray-400 font-medium mb-1">Итог работ</p>
                <p class="text-sm text-gray-800 whitespace-pre-wrap">{{ v.work_summary }}</p>
              </div>

              <!-- Дефекты -->
              <div v-if="v.defects_present" class="bg-orange-50 rounded-lg px-3 py-2">
                <p class="text-xs font-medium text-orange-500 mb-0.5 flex items-center gap-1">
                  <AlertTriangle class="w-3 h-3" />Дефекты
                </p>
                <p v-if="v.defects_summary" class="text-sm text-orange-800 whitespace-pre-wrap">{{ v.defects_summary }}</p>
              </div>

              <!-- Рекомендации -->
              <div v-if="v.recommendations" class="bg-yellow-50 rounded-lg px-3 py-2">
                <p class="text-xs font-medium text-yellow-600 mb-0.5">Рекомендации</p>
                <p class="text-sm text-yellow-800 whitespace-pre-wrap">{{ v.recommendations }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Футер -->
        <div class="px-6 py-4 border-t border-gray-100 flex-shrink-0 flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <button
              @click="goToContractVisits"
              class="btn btn-primary text-sm flex items-center gap-1.5"
            >
              История выездов
              <ArrowRight class="w-4 h-4" />
            </button>
            <RouterLink
              :to="`/contracts/${visitsModal.contractId}`"
              @click="visitsModal.open = false"
              class="btn btn-secondary text-sm flex items-center gap-1"
            >
              Договор
              <ExternalLink class="w-4 h-4" />
            </RouterLink>
          </div>
          <button @click="visitsModal.open = false" class="btn btn-secondary text-sm">Закрыть</button>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import Layout from '../components/Layout.vue'
import { scheduleAPI, visitsAPI } from '../services/api.js'
import { useAuthStore } from '../stores/auth.js'
import { useConfigStore } from '../stores/config.js'
import {
  ChevronLeft, ChevronRight, Calendar as CalendarIcon,
  X, ExternalLink, MessageSquare, Pencil, Search, ArrowRight, AlertTriangle, Printer,
} from 'lucide-vue-next'

const router = useRouter()
const cfg = useConfigStore()

const auth = useAuthStore()
const canEdit = computed(() => auth.hasGroup('admin_group') || auth.hasGroup('office_group'))

const MONTHS_SHORT = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
const MONTHS_FULL  = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

const now = new Date()
const currentYear = ref(now.getFullYear())
const currentMonth = ref(now.getMonth() + 1)
const viewMode = ref('year')
const loading = ref(false)

const rows = ref([])
const monthItems = ref([])
const search = ref('')

const filteredRows = computed(() => {
  if (!search.value.trim()) return rows.value
  const q = search.value.trim().toLowerCase()
  return rows.value.filter(r =>
    r.client_name.toLowerCase().includes(q) ||
    (r.contract_number || '').toLowerCase().includes(q)
  )
})

const filteredMonthItems = computed(() => {
  if (!search.value.trim()) return monthItems.value
  const q = search.value.trim().toLowerCase()
  return monthItems.value.filter(r =>
    r.client_name.toLowerCase().includes(q) ||
    (r.contract_number || '').toLowerCase().includes(q)
  )
})

function isCurrentMonth(month) {
  return currentYear.value === now.getFullYear() && month === (now.getMonth() + 1)
}

function setMode(mode) {
  viewMode.value = mode
  load()
}

function printMonth() {
  const y = currentYear.value
  const m = viewMode.value === 'month' ? currentMonth.value : currentMonth.value
  window.open(`/print/schedule/${y}/${m}`, '_blank')
}

function goNextMonth() {
  viewMode.value = 'month'
  const next = new Date(now.getFullYear(), now.getMonth() + 1, 1)
  currentYear.value = next.getFullYear()
  currentMonth.value = next.getMonth() + 1
  load()
}

async function load() {
  loading.value = true
  try {
    if (viewMode.value === 'year') {
      const res = await scheduleAPI.getYear(currentYear.value)
      rows.value = res.data.rows
    } else {
      const res = await scheduleAPI.getMonth(currentYear.value, currentMonth.value)
      monthItems.value = res.data.items
    }
  } finally {
    loading.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-')
  return `${d}.${m}.${y}`
}

// ---- Модалка клиента ----
const clientModal = ref({ open: false, clientId: null, clientName: '', contractNumber: '', contractId: null })

function openClientModal(row) {
  clientModal.value = {
    open: true,
    clientId: row.client_id,
    clientName: row.client_name || '',
    contractNumber: row.contract_number || '',
    contractId: row.contract_id,
  }
}

// ---- Модалка ячейки ----
const cellModal = ref({ open: false, contractId: null, clientId: null, contractNumber: '', clientName: '', month: null, note: '' })

function openCellModal(row, month, note) {
  cellModal.value = {
    open: true,
    contractId: row.contract_id,
    clientId: row.client_id,
    contractNumber: row.contract_number || '',
    clientName: row.client_name || '',
    month,
    note: note || '',
  }
}

function openEditFromCell() {
  const c = cellModal.value
  cellModal.value.open = false
  openEditModal(c, c.month, c.note)
}

// ---- Модалка редактирования ----
const editModal = ref({ open: false, contractId: null, contractNumber: '', clientName: '', month: null, note: '', originalNote: '' })

function openEditModal(row, month, note) {
  editModal.value = {
    open: true,
    contractId: row.contract_id,
    contractNumber: row.contract_number || '',
    clientName: row.client_name || '',
    month,
    note: note || '',
    originalNote: note || '',
  }
}

async function saveCell() {
  const { contractId, month, note } = editModal.value
  await scheduleAPI.upsertCell(contractId, currentYear.value, month, note)
  editModal.value.open = false
  await load()
}

async function deleteCell() {
  const { contractId, month } = editModal.value
  await scheduleAPI.deleteCell(contractId, currentYear.value, month)
  editModal.value.open = false
  await load()
}

// ---- Модалка комментариев мастеров ----
const visitsModal = ref({ open: false, loading: false, contractId: null, contractNumber: '', clientName: '', visits: [], total: 0 })

async function openVisitsModal(source) {
  clientModal.value.open = false
  cellModal.value.open = false
  const contractId = source.contractId || source.contract_id
  visitsModal.value = {
    open: true,
    loading: true,
    contractId,
    contractNumber: source.contractNumber || source.contract_number || '',
    clientName: source.clientName || source.client_name || '',
    visits: [],
    total: 0,
  }
  try {
    // Берём последние 20 завершённых выездов, фильтруем с комментариями, показываем 5
    const res = await visitsAPI.getAll({ contract_id: contractId, limit: 20 })
    const items = res.data.items || []
    visitsModal.value.visits = items
      .filter(v => v.status === 'done' && (v.work_summary || v.recommendations || v.defects_present))
      .slice(0, 5)
    visitsModal.value.total = res.data.total || 0
  } finally {
    visitsModal.value.loading = false
  }
}

function goToContractVisits() {
  visitsModal.value.open = false
  router.push(`/contracts/${visitsModal.value.contractId}?tab=visits`)
}

// ---- Resize колонки месячного вида ----
const MONTH_COL_KEY = 'schedule-month-col-width'
const monthColWidth = ref(parseInt(localStorage.getItem(MONTH_COL_KEY) || '300'))

function startMonthColResize(e) {
  const startX = e.clientX
  const startW = monthColWidth.value
  const onMove = (ev) => {
    monthColWidth.value = Math.max(120, Math.min(800, startW + ev.clientX - startX))
  }
  const onUp = () => {
    localStorage.setItem(MONTH_COL_KEY, monthColWidth.value)
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

onMounted(load)
</script>
