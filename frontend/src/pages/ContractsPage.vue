<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between flex-wrap gap-y-3 mb-4">
        <div>
          <h1 class="text-xl md:text-3xl font-bold text-gray-900">Договоры</h1>
          <p class="text-gray-600 mt-1">Показано: {{ contracts.length }} из {{ total }}</p>
        </div>
        <button v-if="!auth.isViewer" @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-4 h-4 mr-2" />Новый договор
        </button>
      </div>

      <!-- Фильтры -->
      <div class="card mb-4">
        <button class="md:hidden w-full flex items-center justify-between text-sm font-medium text-gray-700 mb-2" @click="filtersOpen = !filtersOpen">
          <span class="flex items-center gap-2"><Filter class="w-4 h-4" />Фильтры<span v-if="hasActiveFilters" class="w-2 h-2 bg-primary-500 rounded-full inline-block"></span></span>
          <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="filtersOpen ? 'rotate-180' : ''" />
        </button>
        <div :class="filtersOpen ? 'flex' : 'hidden md:flex'" class="flex-wrap gap-3 items-end">
          <div class="relative flex-1 min-w-[200px]">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              v-model="filters.search"
              @input="debouncedLoad"
              placeholder="Поиск по номеру, предмету, клиенту..."
              class="input pl-9 text-sm"
            />
          </div>
          <div class="min-w-[150px]">
            <select v-model="filters.status" @change="load" class="input text-sm">
              <option value="">Все статусы</option>
              <option value="active">Активен</option>
              <option value="closed">Закрыт</option>
              <option value="cancelled">Отменён</option>
            </select>
          </div>
          <button
            v-if="hasActiveFilters"
            @click="resetFilters"
            class="btn btn-secondary text-sm flex items-center gap-1"
          >
            <X class="w-4 h-4" />Сбросить
          </button>
        </div>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
      </div>

      <template v-else>
        <DataTable
          :columns="columns"
          :rows="contracts"
          :masked="auth.isViewer"
          storage-key="contracts-table-v1"
          :total="total"
          :page="page"
          :page-size="pageSize"
          :loading="loading"
          @row-click="onRowClick"
          @update:page="onPageChange"
          @update:page-size="onPageSizeChange"
          @reload="load"
        >
          <!-- Номер -->
          <template #contract_number="{ row }">
            <div
              class="flex items-center gap-2 min-w-0 cursor-pointer"
              @click.stop="openContractQuick(row)"
            >
              <div class="w-7 h-7 bg-blue-100 rounded-md flex-shrink-0 flex items-center justify-center">
                <FileText class="w-4 h-4 text-blue-600" />
              </div>
              <div class="min-w-0">
                <div class="font-medium text-gray-900 truncate hover:text-blue-700 hover:underline">{{ row.contract_number || 'Без номера' }}</div>
                <div v-if="row.subject" class="text-xs text-gray-400 truncate">{{ row.subject }}</div>
              </div>
            </div>
          </template>

          <!-- Клиент -->
          <template #client_name="{ row }">
            <span
              v-if="row.client_name"
              class="truncate block text-gray-700 cursor-pointer hover:text-primary-600 hover:underline"
              @click.stop="row.client_id && openClientQuick(row.client_id)"
            >{{ row.client_name }}</span>
            <span v-else class="text-gray-300">—</span>
          </template>

          <!-- Дата -->
          <template #contract_date="{ row }">
            <span class="text-sm text-gray-700">{{ formatDate(row.contract_date) }}</span>
          </template>

          <!-- Сумма -->
          <template #amount="{ row }">
            <span v-if="row.amount" class="text-sm font-medium text-gray-800">{{ formatAmount(row.amount) }} ₽</span>
            <span v-else class="text-gray-300">—</span>
          </template>

          <!-- Сумма акта -->
          <template #act_amount="{ row }">
            <span v-if="row.act_amount" class="text-sm font-medium text-gray-800">{{ formatAmount(row.act_amount) }} ₽</span>
            <span v-else class="text-gray-300">—</span>
          </template>

          <!-- Объекты -->
          <template #sites_count="{ row }">
            <span
              class="inline-flex items-center gap-1 text-sm font-medium cursor-pointer hover:underline"
              :class="(row.sites_count || 0) > 0 ? 'text-green-700' : 'text-gray-400'"
              @click.stop="(row.sites_count || 0) > 0 && openContractQuick(row)"
            >
              <MapPin class="w-3.5 h-3.5" />{{ row.sites_count ?? 0 }}
            </span>
          </template>

          <!-- Статус -->
          <template #status="{ row }">
            <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="statusClass(row.status)">
              {{ statusLabel(row.status) }}
            </span>
          </template>

          <!-- Действия -->
          <template #actions="{ row }">
            <div class="flex items-center gap-1" @click.stop>
              <router-link
                :to="`/contracts/${row.id}`"
                class="p-1.5 rounded hover:bg-gray-100 text-gray-500 hover:text-primary-600"
                title="Открыть"
              >
                <Eye class="w-4 h-4" />
              </router-link>
              <button
                v-if="auth.hasGroup('admin_group') || auth.hasGroup('office_group')"
                @click="deleteConfirm = row"
                class="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-600"
                title="Удалить"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </template>

          <template #empty>
            <div class="flex flex-col items-center py-8 text-gray-400">
              <FileText class="w-12 h-12 mb-3 text-gray-200" />
              <p>Договоры не найдены</p>
            </div>
          </template>
        </DataTable>

      </template>

      <!-- Quick: Договор -->
      <ContractQuickModal
        v-if="quickContract"
        :contract="quickContract"
        @close="quickContract = null"
        @open-page="router.push(`/contracts/${quickContract.id}`); quickContract = null"
        @open-client="quickContract.client_id && openClientQuick(quickContract.client_id); quickContract = null"
        @open-site="(s) => { quickContract = null; openSiteQuick(s) }"
      />

      <!-- Quick: Объект -->
      <SiteQuickModal
        v-if="quickSite"
        :site="quickSite"
        @close="quickSite = null"
        @open-page="router.push(`/sites/${quickSite.id}`); quickSite = null"
        @open-client="quickSite.client_id && openClientQuick(quickSite.client_id); quickSite = null"
      />

      <!-- Quick: Клиент -->
      <ClientQuickModal
        v-if="quickClient"
        :client="quickClient"
        @close="quickClient = null"
        @open-page="router.push(`/clients/${quickClient.id}`); quickClient = null"
      />

      <!-- Модал создания -->
      <div v-if="createModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 flex flex-col max-h-[90vh]">
          <div class="flex items-center justify-between p-6 border-b flex-shrink-0">
            <h2 class="text-xl font-semibold text-gray-900">Новый договор</h2>
            <button @click="createModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleCreate" class="p-6 space-y-4 overflow-y-auto flex-1">
            <!-- Клиент -->
            <div class="relative" ref="clientDropRef">
              <label class="block text-sm font-medium text-gray-700 mb-1">Клиент</label>
              <input
                v-model="clientSearch"
                @input="onClientSearch"
                @focus="clientDropOpen = true"
                placeholder="Начните вводить название..."
                class="input"
                autocomplete="off"
              />
              <div
                v-if="clientDropOpen && clientOptions.length"
                class="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
              >
                <div
                  v-for="c in clientOptions"
                  :key="c.id"
                  @mousedown.prevent="selectClient(c)"
                  class="px-3 py-2 text-sm cursor-pointer hover:bg-gray-50"
                >{{ c.name }}</div>
              </div>
              <button
                v-if="form.client_id"
                type="button"
                @click="clearClient"
                class="absolute right-2 top-8 text-gray-400 hover:text-gray-600"
              ><X class="w-4 h-4" /></button>
            </div>

            <!-- Объекты клиента -->
            <div v-if="form.client_id">
              <label v-if="clientSites.length" class="block text-sm font-medium text-gray-700 mb-2">Объекты клиента (выберите для привязки)</label>
              <div v-if="clientSites.length" class="border border-gray-200 rounded-lg max-h-36 overflow-y-auto divide-y divide-gray-100">
                <label
                  v-for="s in clientSites"
                  :key="s.id"
                  class="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-gray-50"
                >
                  <input type="checkbox" :value="s.id" v-model="selectedSiteIds" class="rounded border-gray-300 text-primary-600" />
                  <div class="min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate">{{ s.title }}</p>
                    <p class="text-xs text-gray-400 truncate">{{ s.address }}</p>
                  </div>
                </label>
              </div>
              <p v-if="clientSites.length" class="text-xs text-gray-500 mt-1">Выбрано: {{ selectedSiteIds.length }}</p>
              <p v-else-if="!sitesLoading" class="text-sm text-gray-400 bg-gray-50 rounded-lg px-3 py-2">У клиента нет объектов</p>

              <!-- Новые объекты (создаются вместе с договором) -->
              <div v-for="(s, idx) in newSites" :key="idx" class="border border-blue-200 rounded-lg p-3 mt-2 bg-blue-50/30 space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-semibold text-blue-700">Новый объект #{{ idx + 1 }}</span>
                  <button type="button" @click="newSites.splice(idx, 1)" class="text-gray-400 hover:text-red-600"><X class="w-4 h-4" /></button>
                </div>
                <input v-model="s.title" placeholder="Название объекта *" class="input text-sm" />
                <input v-model="s.address" placeholder="Адрес *" class="input text-sm" />
                <input v-model="s.onsite_contact" placeholder="Контакт на месте (необязательно)" class="input text-sm" />
              </div>

              <button
                type="button"
                @click="newSites.push({ title: '', address: '', onsite_contact: '' })"
                class="mt-2 text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
              >
                <Plus class="w-4 h-4" />Создать новый объект
              </button>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Номер договора *</label>
              <input v-model="form.contract_number" class="input" :class="{ 'border-red-400': createErrors.contract_number }" placeholder="0817/2 от 17.08.2006" @input="delete createErrors.contract_number" />
              <p v-if="createErrors.contract_number" class="text-red-600 text-xs mt-1">{{ createErrors.contract_number }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Дата договора</label>
              <input v-model="form.contract_date" type="date" class="input" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Предмет договора</label>
              <input v-model="form.subject" class="input" placeholder="ТО газового оборудования" />
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Сумма договора</label>
                <input v-model="form.amount" type="number" step="0.01" class="input" placeholder="50000" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Сумма акта</label>
                <input v-model="form.act_amount" type="number" step="0.01" class="input" placeholder="50000" />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label>
              <textarea v-model="form.notes" class="input" rows="2" />
            </div>
            <!-- Расписание -->
            <div class="border border-gray-200 rounded-lg overflow-hidden">
              <button
                type="button"
                @click="scheduleEnabled = !scheduleEnabled"
                class="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                :class="scheduleEnabled ? 'bg-blue-50 text-blue-700 hover:bg-blue-50' : ''"
              >
                <span class="flex items-center gap-2">
                  <CalendarDays class="w-4 h-4" />
                  Добавить в расписание
                </span>
                <span class="text-xs px-2 py-0.5 rounded-full" :class="scheduleEnabled ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'">
                  {{ scheduleEnabled ? 'Включено' : 'Выключено' }}
                </span>
              </button>

              <div v-if="scheduleEnabled" class="px-4 pb-4 pt-3 space-y-3 border-t border-gray-100">
                <!-- Год -->
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Год</label>
                  <select v-model="scheduleYear" class="input text-sm">
                    <option v-for="y in SCHEDULE_YEARS" :key="y" :value="y">{{ y }}</option>
                  </select>
                </div>

                <!-- Месяцы -->
                <div>
                  <div class="flex items-center justify-between mb-2">
                    <label class="text-xs font-medium text-gray-600">Месяцы</label>
                    <div class="flex gap-2 text-xs text-blue-600">
                      <button type="button" @click="scheduleMonths = [1,2,3,4,5,6,7,8,9,10,11,12]" class="hover:underline">Все</button>
                      <span class="text-gray-300">|</span>
                      <button type="button" @click="scheduleMonths = []" class="hover:underline">Сбросить</button>
                    </div>
                  </div>
                  <div class="grid grid-cols-3 gap-1.5">
                    <label
                      v-for="(name, idx) in MONTH_NAMES"
                      :key="idx + 1"
                      class="flex items-center gap-2 px-2.5 py-1.5 rounded-md border cursor-pointer text-sm transition-colors"
                      :class="scheduleMonths.includes(idx + 1)
                        ? 'bg-blue-50 border-blue-300 text-blue-700'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
                    >
                      <input
                        type="checkbox"
                        :value="idx + 1"
                        v-model="scheduleMonths"
                        class="rounded border-gray-300 text-blue-600 w-3.5 h-3.5"
                      />
                      {{ name }}
                    </label>
                  </div>
                  <p v-if="scheduleMonths.length" class="text-xs text-gray-500 mt-1.5">Выбрано: {{ scheduleMonths.length }} мес.</p>
                </div>

                <!-- Заметка -->
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Заметка для всех месяцев (необязательно)</label>
                  <textarea v-model="scheduleNote" class="input text-sm" rows="2" placeholder="ТО, осмотр, плановый визит..." />
                </div>
              </div>
            </div>

            <div class="flex justify-end gap-3 pt-2">
              <button type="button" @click="createModalOpen = false" class="btn btn-secondary">Отмена</button>
              <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">
                {{ saving ? 'Сохранение...' : 'Создать' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Delete confirm -->
    <div v-if="deleteConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm mx-4">
        <h3 class="text-lg font-semibold mb-2">Удалить договор?</h3>
        <p class="text-sm text-gray-600 mb-5">
          Договор <strong>{{ deleteConfirm.contract_number || '—' }}</strong> будет удалён безвозвратно.
        </p>
        <div class="flex gap-3">
          <button @click="confirmDelete" :disabled="deleting" class="btn bg-red-600 text-white hover:bg-red-700 flex-1 disabled:opacity-50">
            {{ deleting ? 'Удаление...' : 'Удалить' }}
          </button>
          <button @click="deleteConfirm = null" class="btn btn-secondary flex-1">Отмена</button>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, FileText, X, Search, MapPin, Eye, Trash2, Filter, ChevronDown, CalendarDays } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import ContractQuickModal from '../components/modals/ContractQuickModal.vue'
import SiteQuickModal from '../components/modals/SiteQuickModal.vue'
import ClientQuickModal from '../components/modals/ClientQuickModal.vue'
import { contractsAPI, sitesAPI, clientsAPI, scheduleAPI } from '../services/api.js'
import { useAuthStore } from '../stores/auth.js'
import { useEscClose } from '../composables/useEscClose.js'

const router = useRouter()
const auth = useAuthStore()
const contracts = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const loading = ref(true)
const filtersOpen = ref(false)
const createModalOpen = ref(false)
const saving = ref(false)
const deleteConfirm = ref(null)
const deleting = ref(false)
const form = ref({ contract_number: '', contract_date: '', subject: '', amount: '', act_amount: '', notes: '', client_id: null })
const createErrors = ref({})

// Client search in create modal
const clientSearch = ref('')
const clientOptions = ref([])
const clientDropOpen = ref(false)
const clientDropRef = ref(null)
const clientSites = ref([])
const selectedSiteIds = ref([])
const newSites = ref([])
const sitesLoading = ref(false)

// Schedule в создании договора
const scheduleEnabled = ref(false)
const scheduleYear = ref(new Date().getFullYear())
const scheduleMonths = ref([])
const scheduleNote = ref('')
const MONTH_NAMES = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
const SCHEDULE_YEARS = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() + i)

let clientSearchTimer = null
async function onClientSearch() {
  form.value.client_id = null
  clientSites.value = []
  selectedSiteIds.value = []
  newSites.value = []
  clearTimeout(clientSearchTimer)
  if (!clientSearch.value.trim()) { clientOptions.value = []; return }
  clientSearchTimer = setTimeout(async () => {
    try {
      const res = await clientsAPI.getAll({ search: clientSearch.value, limit: 10 })
      clientOptions.value = res.data.items || res.data
    } catch { clientOptions.value = [] }
  }, 250)
}

async function selectClient(c) {
  form.value.client_id = c.id
  clientSearch.value = c.name
  clientDropOpen.value = false
  clientOptions.value = []
  sitesLoading.value = true
  try {
    const res = await sitesAPI.getAll({ client_id: c.id, limit: 100 })
    clientSites.value = (res.data.items || res.data).filter(s => !s.is_archived)
  } catch { clientSites.value = [] } finally { sitesLoading.value = false }
}

function clearClient() {
  form.value.client_id = null
  clientSearch.value = ''
  clientSites.value = []
  selectedSiteIds.value = []
  newSites.value = []
}

function onClickOutsideClientDrop(e) {
  if (clientDropRef.value && !clientDropRef.value.contains(e.target)) {
    clientDropOpen.value = false
  }
}

// Quick modals
const quickContract = ref(null)
const quickSite = ref(null)
const quickClient = ref(null)

async function openContractQuick(row) {
  try {
    const detail = await contractsAPI.getById(row.id)
    quickContract.value = detail.data
  } catch { /* ignore */ }
}

async function openSiteQuick(site) {
  try {
    const detail = await sitesAPI.getById(site.id)
    quickSite.value = detail.data
  } catch { /* ignore */ }
}

async function openClientQuick(clientId) {
  try {
    const detail = await clientsAPI.getById(clientId)
    quickClient.value = detail.data
  } catch { /* ignore */ }
}

useEscClose([
  { isOpen: () => !!quickSite.value,     close: () => { quickSite.value = null } },
  { isOpen: () => !!quickClient.value,   close: () => { quickClient.value = null } },
  { isOpen: () => !!quickContract.value, close: () => { quickContract.value = null } },
  { isOpen: () => createModalOpen.value, close: () => { createModalOpen.value = false } },
  { isOpen: () => !!deleteConfirm.value, close: () => { deleteConfirm.value = null } },
])

const filters = ref({ search: '', status: '' })
const hasActiveFilters = computed(() => filters.value.search || filters.value.status)

const columns = [
  { key: 'contract_number', label: 'Договор',    width: 260, sortable: true },
  { key: 'client_name',     label: 'Клиент',     width: 200, sortable: true },
  { key: 'contract_date',   label: 'Дата',       width: 120, sortable: true },
  { key: 'amount',          label: 'Сумма',      width: 140, sortable: true },
  { key: 'act_amount',      label: 'Сумма акта', width: 140, sortable: true, defaultVisible: false },
  { key: 'sites_count',     label: 'Объекты',    width: 100, sortable: true },
  { key: 'status',          label: 'Статус',     width: 110, sortable: false },
  { key: 'actions',         label: '',           width: 90,  sortable: false },
]

function onRowClick(_row) {
  // клики обрабатываются в ячейках
}

function buildParams() {
  const p = {
    limit: pageSize.value,
    offset: (page.value - 1) * pageSize.value,
  }
  if (filters.value.search) p.search = filters.value.search
  if (filters.value.status) p.status = filters.value.status
  return p
}

let searchTimer = null
function debouncedLoad() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; load() }, 300)
}

async function load() {
  loading.value = true
  try {
    const res = await contractsAPI.getAll(buildParams())
    contracts.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function onPageChange(p) { page.value = p; load() }
function onPageSizeChange(s) { pageSize.value = s; page.value = 1; load() }

function resetFilters() {
  filters.value = { search: '', status: '' }
  page.value = 1
  load()
}

function openCreate() {
  form.value = { contract_number: '', contract_date: '', subject: '', amount: '', act_amount: '', notes: '', client_id: null }
  createErrors.value = {}
  clientSearch.value = ''
  clientOptions.value = []
  clientSites.value = []
  selectedSiteIds.value = []
  newSites.value = []
  scheduleEnabled.value = false
  scheduleYear.value = new Date().getFullYear()
  scheduleMonths.value = []
  scheduleNote.value = ''
  createModalOpen.value = true
}

async function handleCreate() {
  const e = {}
  if (!form.value.contract_number.trim()) e.contract_number = 'Введите номер договора'
  // Валидация новых объектов: title и address обязательны
  const validNewSites = newSites.value.filter(s => s.title.trim() || s.address.trim())
  for (const s of validNewSites) {
    if (!s.title.trim() || !s.address.trim()) {
      e.contract_number = e.contract_number || 'Заполните название и адрес у нового объекта'
    }
  }
  if (validNewSites.length && !form.value.client_id) {
    e.contract_number = e.contract_number || 'Выберите клиента для нового объекта'
  }
  createErrors.value = e
  if (Object.keys(e).length) return
  saving.value = true
  try {
    const payload = { ...form.value }
    if (!payload.contract_date) delete payload.contract_date
    if (!payload.amount) delete payload.amount
    if (!payload.act_amount) delete payload.act_amount
    if (!payload.client_id) delete payload.client_id
    const res = await contractsAPI.create(payload)
    const newId = res.data.id
    // Создаём новые объекты клиента
    const createdSiteIds = []
    for (const s of validNewSites) {
      const sr = await sitesAPI.create({
        title: s.title.trim(),
        address: s.address.trim(),
        client_id: form.value.client_id,
        onsite_contact: s.onsite_contact?.trim() || null,
      })
      createdSiteIds.push(sr.data.id)
    }
    // Привязываем выбранные + только что созданные объекты
    for (const siteId of [...selectedSiteIds.value, ...createdSiteIds]) {
      await contractsAPI.addSite(newId, siteId)
    }
    // Создаём ячейки расписания
    if (scheduleEnabled.value && scheduleMonths.value.length) {
      const note = scheduleNote.value.trim() || null
      for (const month of scheduleMonths.value) {
        await scheduleAPI.upsertCell(newId, scheduleYear.value, month, note)
      }
    }
    createModalOpen.value = false
    await load()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  deleting.value = true
  try {
    await contractsAPI.delete(deleteConfirm.value.id)
    deleteConfirm.value = null
    await load()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    deleting.value = false
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
function formatAmount(v) { return Number(v).toLocaleString('ru-RU') }

onMounted(() => {
  load()
  document.addEventListener('mousedown', onClickOutsideClientDrop)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', onClickOutsideClientDrop)
})
</script>
