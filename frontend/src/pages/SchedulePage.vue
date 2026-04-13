<template>
  <Layout>
    <div>
      <!-- Заголовок -->
      <div class="flex items-center justify-between flex-wrap gap-y-3 mb-4">
        <div>
          <h1 class="text-xl md:text-3xl font-bold text-gray-900">Расписание</h1>
          <p class="text-gray-600 mt-1">
            <span v-if="viewMode === 'year'">{{ rows.length }} договоров в {{ currentYear }} году</span>
            <span v-else>{{ monthItems.length }} договоров в {{ MONTHS[currentMonth - 1] }} {{ currentYear }}</span>
          </p>
        </div>

        <div class="flex items-center gap-2">
          <!-- Переключатель вида -->
          <div class="flex rounded-lg border border-gray-200 overflow-hidden">
            <button
              @click="viewMode = 'year'"
              :class="viewMode === 'year' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
              class="px-3 py-2 text-sm font-medium transition-colors"
            >Год</button>
            <button
              @click="viewMode = 'month'"
              :class="viewMode === 'month' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
              class="px-3 py-2 text-sm font-medium transition-colors"
            >Месяц</button>
          </div>

          <!-- Навигация по году -->
          <div class="flex items-center gap-1 border border-gray-200 rounded-lg overflow-hidden">
            <button @click="currentYear--; load()" class="px-2 py-2 hover:bg-gray-100 transition-colors">
              <ChevronLeft class="w-4 h-4" />
            </button>
            <span class="px-3 py-2 text-sm font-semibold min-w-[60px] text-center">{{ currentYear }}</span>
            <button @click="currentYear++; load()" class="px-2 py-2 hover:bg-gray-100 transition-colors">
              <ChevronRight class="w-4 h-4" />
            </button>
          </div>

          <!-- Выбор месяца (только в режиме "месяц") -->
          <select
            v-if="viewMode === 'month'"
            v-model="currentMonth"
            @change="load"
            class="input text-sm min-w-[130px]"
          >
            <option v-for="(m, i) in MONTHS" :key="i" :value="i + 1">{{ m }}</option>
          </select>

          <!-- Кнопка "Следующий месяц" -->
          <button
            v-if="viewMode === 'year'"
            @click="goNextMonth"
            class="btn btn-secondary text-sm flex items-center gap-1"
          >
            <CalendarIcon class="w-4 h-4" />
            Следующий месяц
          </button>
        </div>
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
                  <th class="text-left px-3 py-2 font-medium text-gray-600 sticky left-0 bg-gray-50 z-10 min-w-[200px] border-r border-gray-200">
                    Клиент / Договор
                  </th>
                  <th
                    v-for="(m, i) in MONTHS"
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
                  <!-- Клиент / договор (sticky) -->
                  <td class="px-3 py-2 sticky left-0 bg-white z-10 border-r border-gray-200" style="max-width:260px;">
                    <div class="font-medium text-gray-900 truncate text-xs">{{ row.client_name }}</div>
                    <div class="text-gray-400 truncate text-xs">{{ row.contract_number }}</div>
                  </td>
                  <!-- Ячейки месяцев -->
                  <td
                    v-for="(m, i) in MONTHS"
                    :key="i"
                    class="px-1 py-1 text-center align-middle"
                    :class="isCurrentMonth(i + 1) ? 'bg-primary-50/40' : ''"
                  >
                    <div
                      v-if="row.cells[i + 1]"
                      class="group relative"
                      @click="openEdit(row, i + 1, row.cells[i + 1])"
                    >
                      <span
                        class="inline-block px-2 py-1 rounded text-xs font-medium cursor-pointer
                               bg-green-100 text-green-800 hover:bg-green-200 transition-colors
                               max-w-[84px] truncate leading-tight"
                        :title="row.cells[i + 1]"
                      >{{ row.cells[i + 1] }}</span>
                    </div>
                    <button
                      v-else-if="canEdit"
                      @click="openEdit(row, i + 1, '')"
                      class="w-full h-7 text-gray-200 hover:text-gray-400 hover:bg-gray-100 rounded transition-colors text-xs"
                    >+</button>
                  </td>
                </tr>
                <tr v-if="filteredRows.length === 0">
                  <td :colspan="13" class="text-center py-10 text-gray-400">Нет данных за {{ currentYear }} год</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ======= РЕЖИМ: МЕСЯЦ (список) ======= -->
        <div v-else>
          <div v-if="monthItems.length === 0" class="card text-center py-12 text-gray-400">
            Нет записей в {{ MONTHS[currentMonth - 1] }} {{ currentYear }}
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="item in monthItems"
              :key="item.contract_id"
              class="card flex items-center gap-4 cursor-pointer hover:bg-gray-50 transition-colors"
              @click="openEdit(item, currentMonth, item.note)"
            >
              <div class="flex-1 min-w-0">
                <div class="font-medium text-gray-900">{{ item.client_name }}</div>
                <div class="text-sm text-gray-400">{{ item.contract_number }}</div>
              </div>
              <span class="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 flex-shrink-0">
                {{ item.note }}
              </span>
            </div>
          </div>
        </div>

      </template>
    </div>

    <!-- Модалка редактирования ячейки -->
    <div v-if="editModal.open" class="fixed inset-0 z-50 flex items-center justify-center p-4" @keydown.esc="editModal.open = false">
      <div class="absolute inset-0 bg-black/40" @click="editModal.open = false" />
      <div class="relative bg-white rounded-xl shadow-xl p-6 w-full max-w-md z-10">
        <h3 class="text-lg font-semibold mb-1">Ячейка расписания</h3>
        <p class="text-sm text-gray-500 mb-1">{{ editModal.clientName }}</p>
        <p class="text-xs text-gray-400 mb-4">{{ editModal.contractNumber }} — {{ MONTHS[editModal.month - 1] }} {{ currentYear }}</p>

        <label class="block text-sm font-medium text-gray-700 mb-1">Заметка</label>
        <textarea
          v-model="editModal.note"
          rows="3"
          class="input w-full resize-none"
          placeholder="ТО+доки через ЭДО, пролонг..."
          autofocus
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
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Layout from '../components/Layout.vue'
import { scheduleAPI } from '../services/api.js'
import { useAuthStore } from '../stores/auth.js'
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-vue-next'

const auth = useAuthStore()
const canEdit = computed(() => auth.hasGroup('admin_group') || auth.hasGroup('office_group'))

const MONTHS = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']

const now = new Date()
const currentYear = ref(now.getFullYear())
const currentMonth = ref(now.getMonth() + 1)
const viewMode = ref('year')
const loading = ref(false)

// Данные года
const rows = ref([])
// Данные месяца
const monthItems = ref([])

const filteredRows = computed(() => rows.value)

function isCurrentMonth(month) {
  return currentYear.value === now.getFullYear() && month === (now.getMonth() + 1)
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

// Редактирование ячейки
const editModal = ref({
  open: false,
  contractId: null,
  contractNumber: '',
  clientName: '',
  month: null,
  note: '',
  originalNote: '',
})

function openEdit(row, month, note) {
  if (!canEdit.value) return
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

onMounted(load)
</script>
