<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between flex-wrap gap-y-3 mb-6">
        <div>
          <h1 class="text-xl md:text-3xl font-bold text-gray-900">Закупки</h1>
          <p class="text-gray-600 mt-1">Показано: {{ purchases.length }} из {{ total }}</p>
        </div>
        <button v-if="!auth.isViewer" @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-5 h-5 mr-2" />Добавить закупку
        </button>
      </div>

      <!-- Filters -->
      <div class="card mb-4">
        <button class="md:hidden w-full flex items-center justify-between text-sm font-medium text-gray-700 mb-2" @click="filtersOpen = !filtersOpen">
          <span class="flex items-center gap-2"><Filter class="w-4 h-4" />Фильтры<span v-if="filterStatus || filterSiteId || showArchived" class="w-2 h-2 bg-primary-500 rounded-full inline-block"></span></span>
          <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="filtersOpen ? 'rotate-180' : ''" />
        </button>
        <div :class="filtersOpen ? 'flex' : 'hidden md:flex'" class="flex-wrap gap-3 items-end">
          <!-- Статус -->
          <div class="min-w-[160px]">
            <label class="block text-xs text-gray-400 mb-1">Статус</label>
            <select v-model="filterStatus" @change="loadPurchases" class="input text-sm">
              <option value="">Все статусы</option>
              <option v-for="s in cfg.purchaseStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
            </select>
          </div>
          <!-- Объект -->
          <div class="min-w-[200px] flex-1 max-w-xs relative">
            <label class="block text-xs text-gray-400 mb-1">Объект</label>
            <input
              v-model="filterSiteQuery"
              type="text"
              class="input text-sm"
              placeholder="Поиск объекта..."
              autocomplete="off"
              @input="onFilterSiteInput"
              @focus="filterSiteDropdownOpen = true"
              @blur="onFilterSiteBlur"
            />
            <ul
              v-if="filterSiteDropdownOpen && filterSiteResults.length"
              class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
            >
              <li
                @mousedown.prevent="clearFilterSite"
                class="px-3 py-2 text-sm text-gray-400 hover:bg-gray-50 cursor-pointer"
              >— Все объекты —</li>
              <li
                v-for="s in filterSiteResults"
                :key="s.id"
                @mousedown.prevent="selectFilterSite(s)"
                class="px-3 py-2 text-sm hover:bg-gray-50 cursor-pointer truncate"
              >{{ s.title }}</li>
            </ul>
          </div>
          <!-- Архивные -->
          <label v-if="auth.hasGroup('admin_group')" class="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none whitespace-nowrap pb-1">
            <input type="checkbox" v-model="showArchived" @change="loadPurchases" class="rounded" />
            Архивные
          </label>
          <!-- Сброс -->
          <button
            v-if="filterStatus || filterSiteId || showArchived"
            @click="resetPurchaseFilters"
            class="btn btn-secondary text-sm flex items-center gap-1 pb-1"
          >
            <X class="w-4 h-4" />Сбросить
          </button>
        </div>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <DataTable
        v-else
        :columns="columns"
        :rows="purchases"
        :masked="auth.isViewer"
        storage-key="purchases_table"
        :row-class="purchaseRowClass"
        :total="total"
        :page="page"
        :page-size="pageSize"
        :loading="loading"
        @row-click="openDetail"
        @update:page="onPageChange"
        @update:page-size="onPageSizeChange"
        @reload="loadPurchases"
      >
        <template #status="{ row }">
          <div class="flex items-center gap-2" @click.stop>
            <select
              :value="row._newStatus"
              @change="updateStatus(row, $event.target.value)"
              class="input text-sm py-1.5 flex-1"
              :disabled="row.is_archived"
            >
              <option v-for="s in cfg.purchaseStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
            </select>
          </div>
        </template>

        <template #due_date="{ row }">
          {{ formatDate(row.due_date) }}
        </template>

        <template #actions="{ row }">
          <div class="flex items-center gap-1" @click.stop>
            <span v-if="row.is_archived" class="text-xs text-gray-400 italic">Архив</span>
            <template v-else>
              <button
                v-if="row.status === 'installed'"
                @click="archivePurchase(row)"
                class="text-xs text-orange-600 hover:text-orange-800 font-medium px-2 py-1 rounded hover:bg-orange-50"
                title="Перенести в архив"
              >
                В архив
              </button>
            </template>
            <button
              v-if="row.is_archived && auth.hasGroup('admin_group')"
              @click="unarchivePurchase(row)"
              class="text-xs text-blue-600 hover:text-blue-800 font-medium px-2 py-1 rounded hover:bg-blue-50"
            >
              Восстановить
            </button>
            <button
              v-if="auth.hasGroup('admin_group')"
              @click="deletePurchaseConfirm = row"
              class="p-1 rounded hover:bg-red-50 text-gray-400 hover:text-red-600"
              title="Удалить"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </template>

        <template #empty>
          <div class="flex flex-col items-center gap-2">
            <ShoppingCart class="w-12 h-12 text-gray-300" />
            <span>Закупки не найдены</span>
          </div>
        </template>
      </DataTable>

      <!-- Detail / Edit Modal -->
      <div v-if="detailPurchase" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-4 md:p-6 border-b">
            <div>
              <h2 class="text-xl font-semibold text-gray-900">{{ detailPurchase.item }}</h2>
              <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full mt-1" :class="statusBadgeClass(detailPurchase.status)">
                {{ cfg.purchaseStatusLabel(detailPurchase.status) }}
              </span>
            </div>
            <button @click="detailPurchase = null" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleEditSave" class="p-4 md:p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Наименование *</label>
              <input
                v-model="editForm.item"
                class="input"
                :class="{ 'border-red-400': editErrors.item }"
                :disabled="detailPurchase.is_archived"
                @input="delete editErrors.item"
              />
              <p v-if="editErrors.item" class="text-red-600 text-xs mt-1">{{ editErrors.item }}</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Кол-во *</label>
                <input
                  v-model="editForm.qty"
                  type="number" step="0.01" min="0.01"
                  class="input"
                  :class="{ 'border-red-400': editErrors.qty }"
                  :disabled="detailPurchase.is_archived"
                  @input="delete editErrors.qty"
                />
                <p v-if="editErrors.qty" class="text-red-600 text-xs mt-1">{{ editErrors.qty }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Срок</label>
                <input v-model="editForm.due_date" type="date" class="input" :disabled="detailPurchase.is_archived" />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Статус</label>
              <select v-model="editForm.status" class="input" :disabled="detailPurchase.is_archived">
                <option v-for="s in cfg.purchaseStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
              </select>
            </div>
            <div class="relative">
              <label class="block text-sm font-medium text-gray-700 mb-1">Объект</label>
              <input
                v-model="editSiteQuery"
                type="text"
                class="input"
                placeholder="Начните вводить название объекта..."
                autocomplete="off"
                :disabled="detailPurchase.is_archived"
                @input="onEditSiteInput"
                @focus="editSiteDropdownOpen = true"
                @blur="onEditSiteBlur"
              />
              <ul
                v-if="editSiteDropdownOpen && editSiteResults.length"
                class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
              >
                <li
                  @mousedown.prevent="clearEditSite"
                  class="px-3 py-2 text-sm text-gray-400 hover:bg-gray-50 cursor-pointer"
                >— не выбран —</li>
                <li
                  v-for="s in editSiteResults"
                  :key="s.id"
                  @mousedown.prevent="selectEditSite(s)"
                  class="px-3 py-2 text-sm hover:bg-gray-50 cursor-pointer truncate"
                >{{ s.title }}</li>
              </ul>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Дефект</label>
              <select v-model="editForm.defect_id" class="input" :disabled="detailPurchase.is_archived">
                <option :value="null">— не связан —</option>
                <option
                  v-for="d in editFilteredDefects"
                  :key="d.id"
                  :value="d.id"
                >{{ d.title }}{{ d.site_title ? ` (${d.site_title})` : '' }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label>
              <textarea v-model="editForm.notes" class="input" rows="2" :disabled="detailPurchase.is_archived" />
            </div>
            <div class="flex justify-between items-center pt-4">
              <button
                v-if="auth.hasGroup('admin_group')"
                type="button"
                @click="deletePurchaseConfirm = detailPurchase"
                class="btn text-red-600 border border-red-200 hover:bg-red-50 flex items-center gap-1"
              >
                <Trash2 class="w-4 h-4" />Удалить
              </button>
              <div class="flex gap-3 ml-auto">
                <button type="button" @click="detailPurchase = null" class="btn btn-secondary">Отмена</button>
                <button
                  v-if="!detailPurchase.is_archived"
                  type="submit"
                  :disabled="editSaving"
                  class="btn btn-primary disabled:opacity-50"
                >
                  {{ editSaving ? 'Сохранение...' : 'Сохранить' }}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>

      <!-- Create Modal -->
      <div v-if="modalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-4 md:p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">Добавить закупку</h2>
            <button @click="modalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleSave" class="p-4 md:p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Наименование *</label>
              <input
                v-model="form.item"
                class="input"
                :class="{ 'border-red-400': errors.item }"
                placeholder="Насос циркуляционный Grundfos"
                @input="delete errors.item"
              />
              <p v-if="errors.item" class="text-red-600 text-xs mt-1">{{ errors.item }}</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Кол-во *</label>
                <input
                  v-model="form.qty"
                  type="number"
                  step="0.01"
                  min="0.01"
                  class="input"
                  :class="{ 'border-red-400': errors.qty }"
                  @input="delete errors.qty"
                />
                <p v-if="errors.qty" class="text-red-600 text-xs mt-1">{{ errors.qty }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Срок</label>
                <input v-model="form.due_date" type="date" class="input" />
              </div>
            </div>
            <div class="relative">
              <label class="block text-sm font-medium text-gray-700 mb-1">Объект</label>
              <input
                v-model="createSiteQuery"
                type="text"
                class="input"
                placeholder="Начните вводить название объекта..."
                autocomplete="off"
                @input="onCreateSiteInput"
                @focus="createSiteDropdownOpen = true"
                @blur="onCreateSiteBlur"
              />
              <ul
                v-if="createSiteDropdownOpen && createSiteResults.length"
                class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
              >
                <li
                  @mousedown.prevent="clearCreateSite"
                  class="px-3 py-2 text-sm text-gray-400 hover:bg-gray-50 cursor-pointer"
                >— не выбран —</li>
                <li
                  v-for="s in createSiteResults"
                  :key="s.id"
                  @mousedown.prevent="selectCreateSite(s)"
                  class="px-3 py-2 text-sm hover:bg-gray-50 cursor-pointer truncate"
                >{{ s.title }}</li>
              </ul>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Дефект</label>
              <select v-model="form.defect_id" class="input">
                <option :value="null">— не связан —</option>
                <option
                  v-for="d in filteredDefects"
                  :key="d.id"
                  :value="d.id"
                >{{ d.title }}{{ d.site_title ? ` (${d.site_title})` : '' }}</option>
              </select>
              <p class="text-xs text-gray-400 mt-1">Фильтруется по выбранному объекту</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label>
              <textarea v-model="form.notes" class="input" rows="2" />
            </div>
            <div class="flex justify-end gap-3 pt-4">
              <button type="button" @click="modalOpen = false" class="btn btn-secondary">Отмена</button>
              <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">
                {{ saving ? 'Сохранение...' : 'Создать' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Delete purchase confirm -->
    <div v-if="deletePurchaseConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm mx-4">
        <h3 class="text-lg font-semibold mb-2">Удалить закупку?</h3>
        <p class="text-sm text-gray-600 mb-5">
          Закупка <strong>«{{ deletePurchaseConfirm.item }}»</strong> будет удалена безвозвратно.
        </p>
        <div class="flex gap-3">
          <button @click="confirmDeletePurchase" :disabled="deletingPurchase" class="btn bg-red-600 text-white hover:bg-red-700 flex-1 disabled:opacity-50">
            {{ deletingPurchase ? 'Удаление...' : 'Удалить' }}
          </button>
          <button @click="deletePurchaseConfirm = null" class="btn btn-secondary flex-1">Отмена</button>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, ShoppingCart, X, Trash2, Filter, ChevronDown } from 'lucide-vue-next'

import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import { useConfigStore } from '../stores/config.js'
import { useAuthStore } from '../stores/auth.js'
import { purchasesAPI, sitesAPI, defectsAPI } from '../services/api.js'
import { useEscClose } from '../composables/useEscClose.js'

const cfg = useConfigStore()
const auth = useAuthStore()

const purchases = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const defects = ref([])
const loading = ref(true)
const filtersOpen = ref(false)
const filterStatus = ref('')
const filterSiteId = ref('')
const showArchived = ref(false)

// Autocomplete: фильтр по объекту (в шапке)
const filterSiteQuery = ref('')
const filterSiteResults = ref([])
const filterSiteDropdownOpen = ref(false)
let filterSiteTimer = null

async function onFilterSiteInput() {
  filterSiteDropdownOpen.value = true
  clearTimeout(filterSiteTimer)
  filterSiteTimer = setTimeout(async () => {
    const q = filterSiteQuery.value.trim()
    const res = await sitesAPI.getAll({ show_archived: false, limit: 20, search: q || undefined })
    filterSiteResults.value = res.data.items
  }, 250)
}
function selectFilterSite(s) {
  filterSiteId.value = s.id
  filterSiteQuery.value = s.title
  filterSiteDropdownOpen.value = false
  page.value = 1
  loadPurchases()
}
function clearFilterSite() {
  filterSiteId.value = ''
  filterSiteQuery.value = ''
  filterSiteDropdownOpen.value = false
  page.value = 1
  loadPurchases()
}
function onFilterSiteBlur() { setTimeout(() => { filterSiteDropdownOpen.value = false }, 150) }

// Autocomplete: объект в модалке создания
const createSiteQuery = ref('')
const createSiteResults = ref([])
const createSiteDropdownOpen = ref(false)
let createSiteTimer = null

async function onCreateSiteInput() {
  createSiteDropdownOpen.value = true
  form.value.site_id = null
  form.value.defect_id = null
  clearTimeout(createSiteTimer)
  createSiteTimer = setTimeout(async () => {
    const q = createSiteQuery.value.trim()
    const res = await sitesAPI.getAll({ show_archived: false, limit: 20, search: q || undefined })
    createSiteResults.value = res.data.items
  }, 250)
}
function selectCreateSite(s) {
  form.value.site_id = s.id
  form.value.defect_id = null
  createSiteQuery.value = s.title
  createSiteDropdownOpen.value = false
}
function clearCreateSite() {
  form.value.site_id = null
  form.value.defect_id = null
  createSiteQuery.value = ''
  createSiteDropdownOpen.value = false
}
function onCreateSiteBlur() { setTimeout(() => { createSiteDropdownOpen.value = false }, 150) }

// Autocomplete: объект в модалке редактирования
const editSiteQuery = ref('')
const editSiteResults = ref([])
const editSiteDropdownOpen = ref(false)
let editSiteTimer = null

async function onEditSiteInput() {
  editSiteDropdownOpen.value = true
  editForm.value.site_id = null
  editForm.value.defect_id = null
  clearTimeout(editSiteTimer)
  editSiteTimer = setTimeout(async () => {
    const q = editSiteQuery.value.trim()
    const res = await sitesAPI.getAll({ show_archived: false, limit: 20, search: q || undefined })
    editSiteResults.value = res.data.items
  }, 250)
}
function selectEditSite(s) {
  editForm.value.site_id = s.id
  editForm.value.defect_id = null
  editSiteQuery.value = s.title
  editSiteDropdownOpen.value = false
}
function clearEditSite() {
  editForm.value.site_id = null
  editForm.value.defect_id = null
  editSiteQuery.value = ''
  editSiteDropdownOpen.value = false
}
function onEditSiteBlur() { setTimeout(() => { editSiteDropdownOpen.value = false }, 150) }
const modalOpen = ref(false)
const saving = ref(false)
const form = ref({ item: '', qty: 1, due_date: '', notes: '', site_id: null, defect_id: null })
const errors = ref({})

const detailPurchase = ref(null)
const editForm = ref({})
const originalEditForm = ref(null)
const editErrors = ref({})
const editSaving = ref(false)
const deletePurchaseConfirm = ref(null)
const deletingPurchase = ref(false)

useEscClose([
  { isOpen: () => modalOpen.value,                close: () => { modalOpen.value = false } },
  { isOpen: () => !!detailPurchase.value,         close: () => { detailPurchase.value = null } },
  { isOpen: () => !!deletePurchaseConfirm.value,  close: () => { deletePurchaseConfirm.value = null } },
])

// Preload site results при открытии дропдауна фильтра
async function initFilterSites() {
  const res = await sitesAPI.getAll({ show_archived: false, limit: 20 })
  filterSiteResults.value = res.data.items
}

function resetPurchaseFilters() {
  filterStatus.value = ''
  filterSiteId.value = ''
  showArchived.value = false
  page.value = 1
  loadPurchases()
}

const columns = [
  { key: 'item',         label: 'Наименование', width: 220 },
  { key: 'qty',          label: 'Кол-во',       width: 80 },
  { key: 'status',       label: 'Статус',       width: 180, sortable: false },
  { key: 'site_title',   label: 'Объект',       width: 170 },
  { key: 'defect_title', label: 'Дефект',       width: 150, defaultVisible: false },
  { key: 'due_date',     label: 'Срок',         width: 110 },
  { key: 'notes',        label: 'Заметки',      width: 200, defaultVisible: false },
  { key: 'actions',      label: '',             width: 110, sortable: false },
]

// Дефекты, отфильтрованные по выбранному объекту в форме
const filteredDefects = computed(() => {
  if (!form.value.site_id) return defects.value
  return defects.value.filter(d => d.site_id === form.value.site_id)
})

const editFilteredDefects = computed(() => {
  if (!editForm.value.site_id) return defects.value
  return defects.value.filter(d => d.site_id === editForm.value.site_id)
})

function purchaseRowClass(row) {
  if (row.is_archived) return 'opacity-50'
  const m = {
    draft:     'bg-gray-50',
    approved:  'bg-blue-50',
    ordered:   'bg-yellow-50',
    received:  'bg-cyan-50',
    installed: 'bg-orange-50',
    closed:    'bg-green-50',
  }
  return m[row.status] || ''
}

function statusBadgeClass(s) {
  const m = {
    draft:     'bg-gray-100 text-gray-700',
    approved:  'bg-blue-100 text-blue-700',
    ordered:   'bg-yellow-100 text-yellow-800',
    received:  'bg-cyan-100 text-cyan-800',
    installed: 'bg-orange-100 text-orange-700',
    closed:    'bg-green-100 text-green-700',
  }
  return m[s] || 'bg-gray-100 text-gray-700'
}

async function openDetail(row) {
  detailPurchase.value = row
  editForm.value = {
    item:      row.item,
    qty:       row.qty,
    due_date:  row.due_date || '',
    notes:     row.notes || '',
    site_id:   row.site_id || null,
    defect_id: row.defect_id || null,
    status:    row.status,
  }
  originalEditForm.value = { ...editForm.value }
  editErrors.value = {}
  // Инициализируем autocomplete объекта
  editSiteQuery.value = row.site_title || ''
  editSiteDropdownOpen.value = false
  const res = await sitesAPI.getAll({ show_archived: false, limit: 20, search: row.site_title || undefined })
  editSiteResults.value = res.data.items
}

function validateEdit() {
  const e = {}
  if (!editForm.value.item.trim()) e.item = 'Укажите наименование'
  const qty = parseFloat(editForm.value.qty)
  if (!qty || qty <= 0) e.qty = 'Количество должно быть больше 0'
  editErrors.value = e
  return Object.keys(e).length === 0
}

async function handleEditSave() {
  if (!validateEdit()) return
  editSaving.value = true
  try {
    const payload = {
      item:      editForm.value.item.trim(),
      qty:       parseFloat(editForm.value.qty) || 1,
      due_date:  editForm.value.due_date || null,
      notes:     editForm.value.notes || null,
      site_id:   editForm.value.site_id || null,
      defect_id: editForm.value.defect_id || null,
      status:    editForm.value.status,
    }
    if (JSON.stringify(editForm.value) === JSON.stringify(originalEditForm.value)) {
      detailPurchase.value = null
      return
    }
    const res = await purchasesAPI.update(detailPurchase.value.id, payload)
    const idx = purchases.value.findIndex(x => x.id === detailPurchase.value.id)
    if (idx >= 0) purchases.value[idx] = { ...res.data, _newStatus: res.data.status }
    detailPurchase.value = null
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    editSaving.value = false
  }
}

function buildPurchaseParams() {
  const params = {}
  if (filterStatus.value) params.status = filterStatus.value
  if (filterSiteId.value) params.site_id = filterSiteId.value
  if (showArchived.value) params.show_archived = true
  return params
}

async function loadPurchases() {
  loading.value = true
  try {
    const res = await purchasesAPI.getAll({
      ...buildPurchaseParams(),
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
    })
    purchases.value = res.data.items.map((p) => ({ ...p, _newStatus: p.status }))
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function onPageChange(p) { page.value = p; loadPurchases() }
function onPageSizeChange(s) { pageSize.value = s; page.value = 1; loadPurchases() }

async function loadDefects() {
  const res = await defectsAPI.getAll({ limit: 500 })
  defects.value = res.data.items
}

async function updateStatus(p, newStatus) {
  try {
    const res = await purchasesAPI.update(p.id, { status: newStatus })
    const idx = purchases.value.findIndex((x) => x.id === p.id)
    if (idx >= 0) purchases.value[idx] = { ...res.data, _newStatus: res.data.status }
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function archivePurchase(p) {
  try {
    await purchasesAPI.archive(p.id)
    await loadPurchases()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function unarchivePurchase(p) {
  try {
    await purchasesAPI.unarchive(p.id)
    await loadPurchases()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function confirmDeletePurchase() {
  deletingPurchase.value = true
  try {
    await purchasesAPI.delete(deletePurchaseConfirm.value.id)
    deletePurchaseConfirm.value = null
    detailPurchase.value = null
    await loadPurchases()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    deletingPurchase.value = false
  }
}

function validate() {
  const e = {}
  if (!form.value.item.trim()) e.item = 'Укажите наименование'
  const qty = parseFloat(form.value.qty)
  if (!qty || qty <= 0) e.qty = 'Количество должно быть больше 0'
  errors.value = e
  return Object.keys(e).length === 0
}

async function openCreate() {
  form.value = { item: '', qty: 1, due_date: '', notes: '', site_id: null, defect_id: null }
  errors.value = {}
  createSiteQuery.value = ''
  createSiteDropdownOpen.value = false
  modalOpen.value = true
  const res = await sitesAPI.getAll({ show_archived: false, limit: 20 })
  createSiteResults.value = res.data.items
}

async function handleSave() {
  if (!validate()) return
  saving.value = true
  try {
    const payload = {
      item: form.value.item.trim(),
      qty: parseFloat(form.value.qty) || 1,
      due_date: form.value.due_date || null,
      notes: form.value.notes || null,
      site_id: form.value.site_id || null,
      defect_id: form.value.defect_id || null,
    }
    await purchasesAPI.create(payload)
    modalOpen.value = false
    await loadPurchases()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }

onMounted(() => Promise.all([loadPurchases(), loadDefects(), initFilterSites()]))
</script>
