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

      <div v-else class="space-y-4">
        <div v-for="p in purchases" :key="p.id" class="card hover:shadow-md transition-shadow">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <ShoppingCart class="w-5 h-5 text-purple-500" />
                <h3 class="font-semibold text-gray-900">{{ p.item }}</h3>
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="purchaseStatusClass(p.status)">
                  {{ cfg.purchaseStatusLabel(p.status) }}
                </span>
              </div>
              <div class="text-sm text-gray-600 space-y-1">
                <div>Кол-во: {{ p.qty }}</div>
                <div v-if="p.site_title"><Building2 class="w-4 h-4 mr-1 inline" />{{ p.site_title }}</div>
                <div v-if="p.defect_title"><AlertTriangle class="w-4 h-4 mr-1 inline" />{{ p.defect_title }}</div>
                <div v-if="p.due_date"><Calendar class="w-4 h-4 mr-1 inline" />до {{ formatDate(p.due_date) }}</div>
                <div v-if="p.notes" class="text-gray-500 italic">{{ p.notes }}</div>
              </div>
            </div>
            <div class="ml-4 flex flex-col gap-2">
              <select v-model="p._newStatus" @change="updateStatus(p)" class="input text-sm py-1.5">
                <option v-for="s in cfg.purchaseStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
              </select>
            </div>
          </div>
        </div>

        <div v-if="purchases.length === 0" class="text-center py-12 card">
          <ShoppingCart class="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-gray-900">Закупки не найдены</h3>
        </div>
      </div>

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
              <input v-model="form.item" required class="input" placeholder="Насос циркуляционный Grundfos" />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Кол-во</label>
                <input v-model="form.qty" type="number" step="0.01" min="0" class="input" />
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
import { Plus, ShoppingCart, Building2, AlertTriangle, Calendar, X } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { useConfigStore } from '../stores/config.js'
import { purchasesAPI } from '../services/api.js'

const cfg = useConfigStore()
const purchases = ref([])
const loading = ref(true)
const filterStatus = ref('')
const modalOpen = ref(false)
const saving = ref(false)
const form = ref({ item: '', qty: 1, due_date: '', notes: '' })

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

async function updateStatus(p) {
  try {
    const res = await purchasesAPI.update(p.id, { status: p._newStatus })
    const idx = purchases.value.findIndex((x) => x.id === p.id)
    if (idx >= 0) purchases.value[idx] = { ...res.data, _newStatus: res.data.status }
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

function openCreate() {
  form.value = { item: '', qty: 1, due_date: '', notes: '' }
  modalOpen.value = true
}

async function handleSave() {
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

function purchaseStatusClass(s) {
  const m = { draft: 'bg-gray-100 text-gray-600', approved: 'bg-blue-100 text-blue-700', ordered: 'bg-yellow-100 text-yellow-700', received: 'bg-cyan-100 text-cyan-700', installed: 'bg-orange-100 text-orange-700', closed: 'bg-green-100 text-green-700' }
  return m[s] || 'bg-gray-100 text-gray-700'
}
function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }

onMounted(loadPurchases)
</script>
