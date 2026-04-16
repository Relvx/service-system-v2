<template>
  <Layout>
    <div v-if="loading" class="flex justify-center py-16">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
    </div>

    <div v-else-if="contract">
      <!-- Шапка -->
      <div class="flex items-start justify-between flex-wrap gap-y-3 mb-6">
        <div class="flex items-center gap-3 min-w-0">
          <button @click="$router.back()" class="text-gray-500 hover:text-gray-700 mt-1 flex-shrink-0">
            <ArrowLeft class="w-5 h-5" />
          </button>
          <div class="min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <h1 class="text-2xl font-bold text-gray-900">{{ contract.contract_number || 'Без номера' }}</h1>
              <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="statusClass(contract.status)">
                {{ statusLabel(contract.status) }}
              </span>
              <span v-if="contract.is_archived" class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full bg-gray-200 text-gray-600">
                Архив
              </span>
            </div>
            <p v-if="contract.client_name" class="text-gray-500 text-sm mt-0.5">
              <router-link v-if="contract.client_id" :to="`/clients/${contract.client_id}`" class="hover:text-primary-600 hover:underline">
                {{ contract.client_name }}
              </router-link>
              <span v-else>{{ contract.client_name }}</span>
            </p>
          </div>
        </div>
        <button @click="openEdit" class="btn btn-secondary flex items-center">
          <Edit class="w-4 h-4 mr-2" />Редактировать
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Левая колонка -->
        <div class="lg:col-span-1 space-y-4">

          <!-- Основные реквизиты -->
          <div class="card space-y-3">
            <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-400">Реквизиты</h3>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <p class="text-xs text-gray-400 mb-0.5">Дата договора</p>
                <p class="text-sm text-gray-900 font-medium">{{ formatDate(contract.contract_date) }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-0.5">Статус</p>
                <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="statusClass(contract.status)">
                  {{ statusLabel(contract.status) }}
                </span>
              </div>
            </div>

            <div v-if="contract.subject">
              <p class="text-xs text-gray-400 mb-0.5">Предмет договора</p>
              <p class="text-sm text-gray-900">{{ contract.subject }}</p>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <p class="text-xs text-gray-400 mb-0.5">Сумма договора</p>
                <p class="text-sm font-semibold text-gray-900">
                  {{ contract.amount ? formatAmount(contract.amount) + ' ₽' : '—' }}
                </p>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-0.5">Сумма акта</p>
                <p class="text-sm font-semibold text-gray-900">
                  {{ contract.act_amount ? formatAmount(contract.act_amount) + ' ₽' : '—' }}
                </p>
              </div>
            </div>

            <div v-if="contract.notes">
              <p class="text-xs text-gray-400 mb-0.5">Заметки</p>
              <p class="text-sm text-gray-700 whitespace-pre-wrap">{{ contract.notes }}</p>
            </div>

            <div>
              <p class="text-xs text-gray-400 mb-0.5">Создан</p>
              <p class="text-xs text-gray-500">{{ formatDateTime(contract.created_at) }}</p>
            </div>
          </div>

          <!-- Смена статуса -->
          <div class="card space-y-2">
            <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-400">Изменить статус</h3>
            <div class="flex flex-col gap-1.5">
              <button
                v-for="s in statuses" :key="s.value"
                @click="changeStatus(s.value)"
                class="w-full text-left px-3 py-2 rounded-lg text-sm transition-colors"
                :class="contract.status === s.value
                  ? s.activeClass
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100'"
              >
                {{ s.label }}
              </button>
            </div>
          </div>

          <!-- Примечание -->
          <div v-if="contract.description" class="card space-y-2">
            <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-400">Примечание</h3>
            <p class="text-gray-700 whitespace-pre-wrap text-sm">{{ contract.description }}</p>
          </div>

          <!-- История выездов (текстовая) -->
          <div v-if="contract.raw_visit_history" class="card space-y-2">
            <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-400">История (импорт)</h3>
            <p class="text-gray-600 whitespace-pre-wrap text-xs font-mono bg-gray-50 rounded p-2">{{ contract.raw_visit_history }}</p>
          </div>
        </div>

        <!-- Правая колонка: вкладки -->
        <div class="lg:col-span-2 space-y-4">
          <!-- Вкладки -->
          <div class="flex border-b border-gray-200 gap-0">
            <button
              @click="rightTab = 'sites'"
              class="px-4 py-2.5 text-sm font-medium border-b-2 transition-colors"
              :class="rightTab === 'sites' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
            >
              Объекты <span class="ml-1 text-xs text-gray-400">({{ contract.sites.length }})</span>
            </button>
            <button
              @click="rightTab = 'visits'; loadVisits()"
              class="px-4 py-2.5 text-sm font-medium border-b-2 transition-colors"
              :class="rightTab === 'visits' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
            >
              История выездов <span v-if="visits.length" class="ml-1 text-xs text-gray-400">({{ visits.length }})</span><span v-if="!visits.length && visitsLoaded" class="ml-1 text-xs text-gray-400">(0)</span>
            </button>
          </div>

          <!-- Объекты -->
          <div v-if="rightTab === 'sites'" class="card">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-gray-900">Объекты по договору</h3>
              <button @click="addSiteModalOpen = true" class="btn btn-secondary text-sm flex items-center">
                <Plus class="w-4 h-4 mr-1" />Добавить объект
              </button>
            </div>

            <div v-if="contract.sites.length === 0" class="text-center py-10">
              <Building2 class="w-10 h-10 text-gray-300 mx-auto mb-2" />
              <p class="text-gray-500 text-sm">Объекты не привязаны</p>
            </div>

            <div v-else class="space-y-2">
              <div
                v-for="s in contract.sites" :key="s.id"
                class="flex items-center justify-between p-3 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <router-link :to="`/sites/${s.id}`" class="flex items-center gap-3 flex-1 min-w-0">
                  <div class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Building2 class="w-4 h-4 text-green-600" />
                  </div>
                  <div class="min-w-0">
                    <p class="font-medium text-sm text-gray-900 truncate">{{ s.title }}</p>
                    <p class="text-xs text-gray-500 truncate">{{ s.address }}</p>
                  </div>
                  <span v-if="s.is_archived" class="ml-2 flex-shrink-0 text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">Архив</span>
                </router-link>
                <button
                  @click="confirmRemoveSite(s)"
                  class="ml-3 flex-shrink-0 p-1.5 rounded hover:bg-red-50 text-gray-300 hover:text-red-500 transition-colors"
                  title="Убрать из договора"
                >
                  <X class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <!-- История выездов -->
          <div v-if="rightTab === 'visits'">
            <div v-if="visitsLoading" class="flex justify-center py-10">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
            <div v-else-if="visits.length === 0" class="card text-center py-10 text-gray-400">
              <CalendarIcon class="w-10 h-10 mx-auto mb-2 text-gray-300" />
              <p>Выезды по этому договору не найдены</p>
            </div>
            <div v-else class="space-y-3">
              <div
                v-for="v in visits"
                :key="v.id"
                class="card hover:shadow-md transition-shadow cursor-pointer"
                @click="selectedVisit = v"
              >
                <!-- Шапка карточки -->
                <div class="flex items-start justify-between gap-2 mb-2">
                  <div class="min-w-0 flex-1">
                    <p class="font-medium text-gray-900 truncate">{{ v.site_title || '—' }}</p>
                    <p v-if="v.site_address" class="text-xs text-gray-400 truncate">{{ v.site_address }}</p>
                  </div>
                  <span class="inline-flex flex-shrink-0 px-2 py-0.5 text-xs font-medium rounded-full" :class="visitStatusClass(v.status)">
                    {{ visitStatusLabel(v.status) }}
                  </span>
                </div>
                <!-- Метаданные -->
                <div class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500 mb-2">
                  <span class="flex items-center gap-1">
                    <CalendarIcon class="w-3 h-3" />{{ formatDate(v.planned_date) }}
                  </span>
                  <span v-if="v.master_names && v.master_names.length" class="flex items-center gap-1">
                    <User class="w-3 h-3" />{{ v.master_names.join(', ') }}
                  </span>
                  <span v-else-if="v.master_name" class="flex items-center gap-1">
                    <User class="w-3 h-3" />{{ v.master_name }}
                  </span>
                  <span v-if="v.visit_type" class="bg-gray-100 px-1.5 py-0.5 rounded">{{ cfg.visitTypeLabel(v.visit_type) }}</span>
                </div>
                <!-- Результат (для завершённых) -->
                <template v-if="v.work_summary">
                  <div class="border-t pt-2 mt-1">
                    <p class="text-xs font-medium text-gray-400 mb-0.5">Итог работ</p>
                    <p class="text-sm text-gray-700 whitespace-pre-wrap line-clamp-3">{{ v.work_summary }}</p>
                  </div>
                  <div v-if="v.defects_present" class="mt-2 flex items-center gap-1 text-xs text-orange-600 bg-orange-50 rounded px-2 py-1">
                    <AlertTriangle class="w-3 h-3" />
                    <span>Дефекты{{ v.defects_summary ? ': ' + v.defects_summary : '' }}</span>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- Детали выезда (модалка) -->
          <div v-if="selectedVisit" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div class="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
              <div class="flex items-center justify-between p-5 border-b">
                <div class="min-w-0 pr-2">
                  <h2 class="font-semibold text-gray-900 truncate">{{ selectedVisit.site_title }}</h2>
                  <p v-if="selectedVisit.site_address" class="text-xs text-gray-400 truncate">{{ selectedVisit.site_address }}</p>
                </div>
                <button @click="selectedVisit = null" class="text-gray-400 hover:text-gray-600 flex-shrink-0"><X class="w-5 h-5" /></button>
              </div>
              <div class="p-5 space-y-4">
                <div class="flex flex-wrap gap-2">
                  <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="visitStatusClass(selectedVisit.status)">
                    {{ visitStatusLabel(selectedVisit.status) }}
                  </span>
                  <span v-if="selectedVisit.visit_type" class="inline-flex px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">
                    {{ cfg.visitTypeLabel(selectedVisit.visit_type) }}
                  </span>
                </div>
                <div class="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p class="text-xs text-gray-400">Дата</p>
                    <p class="font-medium">{{ formatDate(selectedVisit.planned_date) }}</p>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400">Мастер</p>
                    <p class="font-medium">{{ (selectedVisit.master_names && selectedVisit.master_names.length) ? selectedVisit.master_names.join(', ') : (selectedVisit.master_name || '—') }}</p>
                  </div>
                </div>
                <div v-if="selectedVisit.office_notes" class="bg-blue-50 rounded-lg p-3">
                  <p class="text-xs font-medium text-blue-600 mb-1">Заметка офиса</p>
                  <p class="text-sm text-blue-800">{{ selectedVisit.office_notes }}</p>
                </div>
                <template v-if="selectedVisit.work_summary">
                  <div>
                    <p class="text-xs font-medium text-gray-400 mb-1">Итог работ</p>
                    <p class="text-sm text-gray-800 whitespace-pre-wrap">{{ selectedVisit.work_summary }}</p>
                  </div>
                  <div v-if="selectedVisit.defects_present" class="bg-orange-50 rounded-lg p-3">
                    <p class="text-xs font-medium text-orange-600 mb-1">⚠ Дефекты</p>
                    <p v-if="selectedVisit.defects_summary" class="text-sm text-orange-800">{{ selectedVisit.defects_summary }}</p>
                  </div>
                  <div v-if="selectedVisit.recommendations" class="bg-yellow-50 rounded-lg p-3">
                    <p class="text-xs font-medium text-yellow-600 mb-1">Рекомендации</p>
                    <p class="text-sm text-yellow-800">{{ selectedVisit.recommendations }}</p>
                  </div>
                </template>
                <div v-else class="text-sm text-gray-400 italic">Комментариев мастера нет</div>
              </div>
              <div class="flex justify-end p-5 border-t">
                <button @click="selectedVisit = null" class="btn btn-primary">Закрыть</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модал редактирования -->
    <div v-if="editModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-lg flex flex-col max-h-[90vh]">
        <div class="flex items-center justify-between p-4 md:p-6 border-b flex-shrink-0">
          <h2 class="text-xl font-semibold text-gray-900">Редактировать договор</h2>
          <button @click="editModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleEditSave" class="p-4 md:p-6 space-y-4 overflow-y-auto flex-1">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Номер договора</label>
            <input v-model="editForm.contract_number" class="input" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Дата договора</label>
            <input v-model="editForm.contract_date" type="date" class="input" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Предмет договора</label>
            <input v-model="editForm.subject" class="input" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Сумма договора</label>
              <input v-model="editForm.amount" type="number" step="0.01" class="input" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Сумма акта</label>
              <input v-model="editForm.act_amount" type="number" step="0.01" class="input" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label>
            <textarea v-model="editForm.notes" class="input" rows="3" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Примечание</label>
            <textarea v-model="editForm.description" class="input" rows="3" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">История выездов (текст)</label>
            <textarea v-model="editForm.raw_visit_history" class="input" rows="4" placeholder="Например: 15.02.2024 Клочков ТО; 18.05.2024 Ильяс ТО" />
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="editModalOpen = false" class="btn btn-secondary">Отмена</button>
            <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">
              {{ saving ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Модал добавления объекта -->
    <div v-if="addSiteModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between p-4 md:p-6 border-b">
          <h2 class="text-xl font-semibold text-gray-900">Добавить объект</h2>
          <button @click="addSiteModalOpen = false; siteSearch = ''; siteResults = []" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <div class="p-4 md:p-6 space-y-4">
          <input
            v-model="siteSearch"
            placeholder="Поиск объекта по названию или адресу..."
            class="input"
            @input="searchSites"
          />
          <div v-if="siteResults.length > 0" class="space-y-2 max-h-64 overflow-y-auto">
            <button
              v-for="s in siteResults" :key="s.id"
              @click="handleAddSite(s.id)"
              class="w-full text-left p-3 bg-gray-50 hover:bg-primary-50 rounded-lg transition-colors"
            >
              <p class="font-medium text-sm text-gray-900">{{ s.title }}</p>
              <p class="text-xs text-gray-500">{{ s.address }}</p>
            </button>
          </div>
          <p v-else-if="siteSearch.length > 1" class="text-sm text-gray-500 text-center py-4">Ничего не найдено</p>
          <p v-else class="text-sm text-gray-400 text-center py-2">Введите минимум 2 символа</p>
        </div>
      </div>
    </div>

    <!-- Подтверждение удаления объекта -->
    <div v-if="removeSiteConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-4 md:p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Убрать объект?</h2>
        <p class="text-gray-600 mb-6">Объект <strong>{{ removeSiteConfirm.title }}</strong> будет убран из договора.</p>
        <div class="flex justify-end gap-3">
          <button @click="removeSiteConfirm = null" class="btn btn-secondary">Отмена</button>
          <button @click="handleRemoveSite" class="btn bg-red-600 text-white hover:bg-red-700">Убрать</button>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Edit, Plus, X, Building2, Calendar as CalendarIcon, User, AlertTriangle } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { contractsAPI, sitesAPI, visitsAPI } from '../services/api.js'
import { useConfigStore } from '../stores/config.js'
import { useEscClose } from '../composables/useEscClose.js'

const cfg = useConfigStore()

const route = useRoute()
const contract = ref(null)
const loading = ref(true)
const saving = ref(false)

const editModalOpen = ref(false)
const editForm = ref({})

const rightTab = ref('sites')
const visits = ref([])
const visitsLoading = ref(false)
const selectedVisit = ref(null)
let visitsLoaded = false

async function loadVisits() {
  if (visitsLoaded) return
  visitsLoading.value = true
  try {
    const res = await visitsAPI.getAll({ contract_id: route.params.id, limit: 200 })
    visits.value = res.data.items
    visitsLoaded = true
  } finally {
    visitsLoading.value = false
  }
}

function visitStatusClass(s) {
  const m = { planned: 'bg-blue-100 text-blue-700', in_progress: 'bg-green-100 text-green-700', done: 'bg-gray-200 text-gray-600', closed: 'bg-gray-200 text-gray-600', cancelled: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-600'
}
function visitStatusLabel(s) {
  const m = { planned: 'Запланирован', in_progress: 'В работе', done: 'Завершён', closed: 'Закрыт', cancelled: 'Отменён' }
  return m[s] || s
}

const addSiteModalOpen = ref(false)
const siteSearch = ref('')
const siteResults = ref([])
const removeSiteConfirm = ref(null)

useEscClose([
  { isOpen: () => !!selectedVisit.value,        close: () => { selectedVisit.value = null } },
  { isOpen: () => editModalOpen.value,          close: () => { editModalOpen.value = false } },
  { isOpen: () => addSiteModalOpen.value,       close: () => { addSiteModalOpen.value = false; siteSearch.value = ''; siteResults.value = [] } },
  { isOpen: () => !!removeSiteConfirm.value,    close: () => { removeSiteConfirm.value = null } },
])

const statuses = [
  { value: 'active',    label: 'Активен',  activeClass: 'bg-green-100 text-green-700 font-medium' },
  { value: 'closed',   label: 'Закрыт',   activeClass: 'bg-gray-200 text-gray-700 font-medium' },
  { value: 'cancelled', label: 'Отменён', activeClass: 'bg-red-100 text-red-700 font-medium' },
]

async function load() {
  loading.value = true
  try {
    const res = await contractsAPI.getById(route.params.id)
    contract.value = res.data
  } finally {
    loading.value = false
  }
}

function openEdit() {
  editForm.value = {
    contract_number: contract.value.contract_number || '',
    contract_date: contract.value.contract_date || '',
    subject: contract.value.subject || '',
    amount: contract.value.amount || '',
    act_amount: contract.value.act_amount || '',
    notes: contract.value.notes || '',
    description: contract.value.description || '',
    raw_visit_history: contract.value.raw_visit_history || '',
  }
  editModalOpen.value = true
}

async function handleEditSave() {
  saving.value = true
  try {
    const payload = { ...editForm.value }
    if (!payload.contract_date) payload.contract_date = null
    if (!payload.amount) payload.amount = null
    if (!payload.act_amount) payload.act_amount = null
    await contractsAPI.update(contract.value.id, payload)
    editModalOpen.value = false
    await load()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function changeStatus(status) {
  if (contract.value.status === status) return
  try {
    await contractsAPI.update(contract.value.id, { status })
    contract.value.status = status
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

let searchTimeout = null
async function searchSites() {
  clearTimeout(searchTimeout)
  if (siteSearch.value.length < 2) { siteResults.value = []; return }
  searchTimeout = setTimeout(async () => {
    const res = await sitesAPI.getAll({ search: siteSearch.value, limit: 50 })
    const linked = new Set(contract.value.sites.map(s => s.id))
    siteResults.value = res.data.items.filter(s => !linked.has(s.id)).slice(0, 10)
  }, 300)
}

async function handleAddSite(siteId) {
  try {
    await contractsAPI.addSite(contract.value.id, siteId)
    addSiteModalOpen.value = false
    siteSearch.value = ''
    siteResults.value = []
    await load()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

function confirmRemoveSite(site) {
  removeSiteConfirm.value = site
}

async function handleRemoveSite() {
  try {
    await contractsAPI.removeSite(contract.value.id, removeSiteConfirm.value.id)
    removeSiteConfirm.value = null
    await load()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

function statusClass(s) {
  const m = { active: 'bg-green-100 text-green-700', closed: 'bg-gray-200 text-gray-600', cancelled: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-600'
}
function statusLabel(s) {
  const m = { active: 'Активен', closed: 'Закрыт', cancelled: 'Отменён' }
  return m[s] || s
}
function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }
function formatDateTime(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function formatAmount(v) { return Number(v).toLocaleString('ru-RU') }

onMounted(async () => {
  await load()
  // Если в URL ?tab=visits — сразу открываем вкладку выездов
  if (route.query.tab === 'visits') {
    rightTab.value = 'visits'
    await nextTick()
    loadVisits()
  }
})

watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) load()
})
</script>
