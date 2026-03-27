<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between mb-4">
        <div>
          <h1 class="text-xl md:text-3xl font-bold text-gray-900">Клиенты</h1>
          <p class="text-gray-600 mt-1">Показано: {{ clients.length }} из {{ total }}</p>
        </div>
        <button @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-5 h-5 mr-2" />Добавить клиента
        </button>
      </div>

      <!-- Фильтры -->
      <div class="card mb-4">
        <div class="flex flex-wrap gap-3 items-end">
          <!-- Поиск -->
          <div class="relative flex-1 min-w-[200px]">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              v-model="filters.search"
              @input="debouncedLoad"
              type="text"
              placeholder="Поиск по названию, ИНН, контакту..."
              class="input pl-9 text-sm"
            />
          </div>

          <!-- Статус -->
          <div class="min-w-[150px]">
            <select v-model="filters.status" @change="loadClients" class="input text-sm">
              <option value="">Все статусы</option>
              <option value="active">Активные</option>
              <option value="inactive">Неактивные</option>
            </select>
          </div>

          <!-- Архивные (только admin) -->
          <label v-if="auth.hasGroup('admin_group')" class="flex items-center gap-2 cursor-pointer text-sm text-gray-600 whitespace-nowrap">
            <input type="checkbox" v-model="filters.showArchived" @change="loadClients" class="rounded" />
            Архивные
          </label>

          <!-- Сброс фильтров -->
          <button
            v-if="hasActiveFilters"
            @click="resetFilters"
            class="btn btn-secondary text-sm flex items-center gap-1"
          >
            <X class="w-4 h-4" />Сбросить
          </button>
        </div>
      </div>

      <!-- Таблица -->
      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <template v-else>
        <DataTable
          :columns="columns"
          :rows="clients"
          storage-key="clients-table-v1"
          :row-class="rowClass"
          @row-click="onRowClick"
        >
          <!-- Название -->
          <template #name="{ row }">
            <div class="flex items-center gap-2 min-w-0">
              <div class="w-7 h-7 bg-primary-100 rounded-md flex-shrink-0 flex items-center justify-center">
                <Building2 class="w-4 h-4 text-primary-600" />
              </div>
              <div class="min-w-0">
                <div class="font-medium text-gray-900 truncate">{{ row.name }}</div>
                <div v-if="row.inn" class="text-xs text-gray-400 truncate">ИНН: {{ row.inn }}</div>
              </div>
            </div>
          </template>

          <!-- Контакт -->
          <template #contacts="{ row }">
            <div class="min-w-0">
              <div v-if="row.contact_person" class="truncate text-gray-800">{{ row.contact_person }}</div>
              <div v-if="row.contacts" class="text-xs text-gray-500 truncate">{{ row.contacts.split(',')[0] }}</div>
              <span v-if="!row.contact_person && !row.contacts" class="text-gray-300">—</span>
            </div>
          </template>

          <!-- Объекты -->
          <template #sites_count="{ row }">
            <span
              class="inline-flex items-center gap-1 text-sm font-medium cursor-pointer hover:underline"
              :class="row.sites_count > 0 ? 'text-blue-700' : 'text-gray-400'"
              @click.stop="row.sites_count > 0 && router.push(`/clients/${row.id}?tab=sites`)"
            >
              <MapPin class="w-3.5 h-3.5" />{{ row.sites_count ?? 0 }}
            </span>
          </template>

          <!-- Договоры -->
          <template #contracts_count="{ row }">
            <span
              class="inline-flex items-center gap-1 text-sm font-medium cursor-pointer hover:underline"
              :class="row.contracts_count > 0 ? 'text-violet-700' : 'text-gray-400'"
              @click.stop="row.contracts_count > 0 && router.push(`/clients/${row.id}?tab=contracts`)"
            >
              <FileText class="w-3.5 h-3.5" />{{ row.contracts_count ?? 0 }}
            </span>
          </template>

          <!-- Выезды -->
          <template #visits_count="{ row }">
            <span
              class="inline-flex items-center gap-1 text-sm font-medium cursor-pointer hover:underline"
              :class="row.visits_count > 0 ? 'text-green-700' : 'text-gray-400'"
              @click.stop="row.visits_count > 0 && router.push(`/clients/${row.id}?tab=visits`)"
            >
              <CalendarCheck class="w-3.5 h-3.5" />{{ row.visits_count ?? 0 }}
            </span>
          </template>

          <!-- Статус -->
          <template #status="{ row }">
            <span v-if="row.is_archived" class="badge bg-gray-100 text-gray-500 text-xs px-2 py-0.5 rounded-full">Архив</span>
            <span v-else-if="row.is_active" class="badge bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full">Активен</span>
            <span v-else class="badge bg-yellow-100 text-yellow-700 text-xs px-2 py-0.5 rounded-full">Неактивен</span>
          </template>

          <!-- Действия -->
          <template #actions="{ row }">
            <div class="flex items-center gap-1" @click.stop>
              <button
                v-if="!row.is_archived"
                @click="openEdit(row)"
                class="p-1.5 rounded hover:bg-gray-100 text-gray-500 hover:text-gray-700"
                title="Редактировать"
              >
                <Edit class="w-4 h-4" />
              </button>
              <button
                v-if="!row.is_archived"
                @click="archiveConfirm = row"
                class="p-1.5 rounded hover:bg-amber-50 text-gray-400 hover:text-amber-600"
                title="В архив"
              >
                <Archive class="w-4 h-4" />
              </button>
              <button
                v-if="row.is_archived && auth.hasGroup('admin_group')"
                @click="handleUnarchive(row)"
                class="p-1.5 rounded hover:bg-green-50 text-gray-400 hover:text-green-600"
                title="Восстановить"
              >
                <ArchiveRestore class="w-4 h-4" />
              </button>
            </div>
          </template>

          <template #empty>
            <div class="flex flex-col items-center py-8 text-gray-400">
              <Building2 class="w-12 h-12 mb-3 text-gray-200" />
              <p>Клиенты не найдены</p>
            </div>
          </template>
        </DataTable>

        <!-- Infinite scroll sentinel -->
        <div ref="sentinelRef" class="h-4 mt-2"></div>
        <div v-if="loadingMore" class="flex justify-center py-4">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      </template>

      <!-- Create / Edit Modal -->
      <div v-if="modalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">
              {{ editing ? 'Редактировать клиента' : 'Добавить клиента' }}
            </h2>
            <button @click="modalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleSave" class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
              <input v-model="form.name" class="input" :class="{ 'border-red-400': errors.name }" placeholder='ООО "Название"' @input="delete errors.name" />
              <p v-if="errors.name" class="text-red-600 text-xs mt-1">{{ errors.name }}</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">ИНН</label>
                <input v-model="form.inn" class="input" :class="{ 'border-red-400': errors.inn }" placeholder="1234567890" @input="delete errors.inn" />
                <p v-if="errors.inn" class="text-red-600 text-xs mt-1">{{ errors.inn }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">КПП</label>
                <input v-model="form.kpp" class="input" :class="{ 'border-red-400': errors.kpp }" placeholder="123456789" @input="delete errors.kpp" />
                <p v-if="errors.kpp" class="text-red-600 text-xs mt-1">{{ errors.kpp }}</p>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Контактное лицо</label>
              <input v-model="form.contact_person" class="input" placeholder="Иванов Иван" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Контакты</label>
              <input v-model="form.contacts" class="input" placeholder="8-495-123-45-67" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label>
              <textarea v-model="form.notes" class="input" rows="3" placeholder="Дополнительная информация..." />
            </div>
            <div class="flex justify-end gap-3 pt-4">
              <button type="button" @click="modalOpen = false" class="btn btn-secondary">Отмена</button>
              <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">
                {{ saving ? 'Сохранение...' : (editing ? 'Сохранить' : 'Создать') }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Archive Confirm -->
      <div v-if="archiveConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Отправить в архив?</h2>
          <p class="text-gray-600 mb-1">Клиент <strong>{{ archiveConfirm.name }}</strong> будет скрыт из основного списка.</p>
          <p class="text-sm text-gray-500 mb-6">Все данные и история выездов сохранятся.</p>
          <div class="flex justify-end gap-3">
            <button @click="archiveConfirm = null" class="btn btn-secondary">Отмена</button>
            <button @click="handleArchive" class="btn bg-amber-600 text-white hover:bg-amber-700">В архив</button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search, Plus, Building2, Edit, Archive, ArchiveRestore, X,
  MapPin, FileText, CalendarCheck,
} from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import { clientsAPI } from '../services/api.js'
import { useAuthStore } from '../stores/auth.js'
import { useEscClose } from '../composables/useEscClose.js'

const router = useRouter()
const auth = useAuthStore()

const clients = ref([])
const total = ref(0)
const loading = ref(true)
const loadingMore = ref(false)
const modalOpen = ref(false)
const editing = ref(null)
const archiveConfirm = ref(null)
const saving = ref(false)
const form = ref({ name: '', inn: '', kpp: '', contact_person: '', contacts: '', notes: '' })
const originalForm = ref(null)
const errors = ref({})

useEscClose([
  { isOpen: () => modalOpen.value,        close: () => { modalOpen.value = false } },
  { isOpen: () => !!archiveConfirm.value, close: () => { archiveConfirm.value = null } },
])

const filters = ref({
  search: '',
  status: '',      // '' | 'active' | 'inactive'
  showArchived: false,
})

const hasActiveFilters = computed(() =>
  filters.value.search || filters.value.status || filters.value.showArchived
)

const columns = [
  { key: 'name',            label: 'Клиент',      width: 280, sortable: true },
  { key: 'contacts',        label: 'Контакт',     width: 180, sortable: false },
  { key: 'sites_count',     label: 'Объекты',     width: 100, sortable: true },
  { key: 'contracts_count', label: 'Договоры',    width: 110, sortable: true },
  { key: 'visits_count',    label: 'Выезды',      width: 100, sortable: true },
  { key: 'status',          label: 'Статус',      width: 120, sortable: false },
  { key: 'actions',         label: '',            width: 90,  sortable: false },
]

function rowClass(row) {
  return row.is_archived ? 'opacity-60 bg-gray-50' : ''
}

function onRowClick(row) {
  if (!row.is_archived) router.push(`/clients/${row.id}`)
}

const LIMIT = 50
const sentinelRef = ref(null)
let observer = null

function buildParams(offset = 0) {
  const p = { limit: LIMIT, offset, show_archived: filters.value.showArchived || undefined }
  if (filters.value.search) p.search = filters.value.search
  if (filters.value.status === 'active') p.active_only = true
  // 'inactive' — нет серверного фильтра, фильтруем на клиенте
  return p
}

async function loadClients() {
  loading.value = true
  try {
    const res = await clientsAPI.getAll(buildParams(0))
    let items = res.data.items
    if (filters.value.status === 'inactive') items = items.filter(c => !c.is_active && !c.is_archived)
    clients.value = items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || clients.value.length >= total.value) return
  loadingMore.value = true
  try {
    const res = await clientsAPI.getAll(buildParams(clients.value.length))
    let items = res.data.items
    if (filters.value.status === 'inactive') items = items.filter(c => !c.is_active && !c.is_archived)
    clients.value.push(...items)
    total.value = res.data.total
  } finally {
    loadingMore.value = false
  }
}

let searchTimer = null
function debouncedLoad() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadClients, 300)
}

function resetFilters() {
  filters.value = { search: '', status: '', showArchived: false }
  loadClients()
}

function setupObserver() {
  if (observer) observer.disconnect()
  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) loadMore()
  }, { threshold: 0.1 })
  if (sentinelRef.value) observer.observe(sentinelRef.value)
}

function validate() {
  const e = {}
  if (!form.value.name.trim()) e.name = 'Введите название'
  if (form.value.inn && !/^\d{10}(\d{2})?$/.test(form.value.inn)) e.inn = 'ИНН должен содержать 10 или 12 цифр'
  if (form.value.kpp && !/^\d{9}$/.test(form.value.kpp)) e.kpp = 'КПП должен содержать 9 цифр'
  errors.value = e
  return Object.keys(e).length === 0
}

function openCreate() {
  editing.value = null
  errors.value = {}
  form.value = { name: '', inn: '', kpp: '', contact_person: '', contacts: '', notes: '' }
  modalOpen.value = true
}

function openEdit(c) {
  editing.value = c
  errors.value = {}
  form.value = { name: c.name, inn: c.inn || '', kpp: c.kpp || '', contact_person: c.contact_person || '', contacts: c.contacts || '', notes: c.notes || '' }
  originalForm.value = { ...form.value }
  modalOpen.value = true
}

async function handleSave() {
  if (!validate()) return
  saving.value = true
  try {
    if (editing.value) {
      if (JSON.stringify(form.value) === JSON.stringify(originalForm.value)) {
        modalOpen.value = false
        return
      }
      await clientsAPI.update(editing.value.id, form.value)
    } else {
      await clientsAPI.create(form.value)
    }
    modalOpen.value = false
    errors.value = {}
    await loadClients()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function handleArchive() {
  try {
    await clientsAPI.archive(archiveConfirm.value.id)
    archiveConfirm.value = null
    await loadClients()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleUnarchive(c) {
  try {
    await clientsAPI.unarchive(c.id)
    await loadClients()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(async () => {
  await loadClients()
  setupObserver()
})
onUnmounted(() => { if (observer) observer.disconnect() })
</script>
