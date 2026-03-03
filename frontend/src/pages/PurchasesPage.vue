<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Закупки</h1>
          <p class="text-gray-600 mt-1">Всего: {{ purchases.length }}</p>
        </div>
        <button @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-5 h-5 mr-2" />Добавить закупку
        </button>
      </div>

      <div class="card mb-6">
        <div class="flex gap-4">
          <select v-model="filterStatus" @change="loadPurchases" class="input flex-1">
            <option value="">Все статусы</option>
            <option v-for="s in cfg.purchaseStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
          </select>
          <button @click="loadPurchases" class="btn btn-primary">Обновить</button>
        </div>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <DataTable v-else :columns="columns" :rows="purchases" storage-key="purchases_table">
        <template #status="{ row }">
          <select
            :value="row._newStatus"
            @change="updateStatus(row, $event.target.value)"
            class="input text-sm py-1.5"
          >
            <option v-for="s in cfg.purchaseStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
          </select>
        </template>

        <template #due_date="{ row }">
          {{ formatDate(row.due_date) }}
        </template>

        <template #empty>
          <div class="flex flex-col items-center gap-2">
            <ShoppingCart class="w-12 h-12 text-gray-300" />
            <span>Закупки не найдены</span>
          </div>
        </template>
      </DataTable>

      <!-- Create Modal -->
      <div v-if="modalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">Добавить закупку</h2>
            <button @click="modalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleSave" class="p-6 space-y-4">
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
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Кол-во</label>
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
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, ShoppingCart, X } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import { useConfigStore } from '../stores/config.js'
import { purchasesAPI } from '../services/api.js'

const cfg = useConfigStore()
const purchases = ref([])
const loading = ref(true)
const filterStatus = ref('')
const modalOpen = ref(false)
const saving = ref(false)
const form = ref({ item: '', qty: 1, due_date: '', notes: '' })
const errors = ref({})

const columns = [
  { key: 'item',         label: 'Наименование', width: 220 },
  { key: 'qty',          label: 'Кол-во',       width: 80 },
  { key: 'status',       label: 'Статус',       width: 160, sortable: false },
  { key: 'site_title',   label: 'Объект',       width: 170 },
  { key: 'defect_title', label: 'Дефект',       width: 150, defaultVisible: false },
  { key: 'due_date',     label: 'Срок',         width: 120 },
  { key: 'notes',        label: 'Заметки',      width: 200, defaultVisible: false },
]

async function loadPurchases() {
  loading.value = true
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    const res = await purchasesAPI.getAll(params)
    purchases.value = res.data.map((p) => ({ ...p, _newStatus: p.status }))
  } finally {
    loading.value = false
  }
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

function validate() {
  const e = {}
  if (!form.value.item.trim()) e.item = 'Укажите наименование'
  const qty = parseFloat(form.value.qty)
  if (!qty || qty <= 0) e.qty = 'Количество должно быть больше 0'
  errors.value = e
  return Object.keys(e).length === 0
}

function openCreate() {
  form.value = { item: '', qty: 1, due_date: '', notes: '' }
  errors.value = {}
  modalOpen.value = true
}

async function handleSave() {
  if (!validate()) return
  saving.value = true
  try {
    await purchasesAPI.create({ ...form.value, qty: parseFloat(form.value.qty) || 1, due_date: form.value.due_date || null })
    modalOpen.value = false
    await loadPurchases()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }

onMounted(loadPurchases)
</script>
