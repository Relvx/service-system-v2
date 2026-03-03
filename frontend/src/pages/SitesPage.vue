<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Объекты</h1>
          <p class="text-gray-600 mt-1">Всего объектов: {{ sites.length }}</p>
        </div>
        <button @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-5 h-5 mr-2" />Добавить объект
        </button>
      </div>

      <div class="card mb-6">
        <div class="flex gap-4 flex-wrap">
          <div class="flex-1 relative min-w-[200px]">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input v-model="search" @keyup.enter="loadSites" type="text" placeholder="Поиск по названию или адресу..." class="input pl-10" />
          </div>
          <button @click="loadSites" class="btn btn-primary">Найти</button>
          <label v-if="auth.hasGroup('admin_group')" class="flex items-center gap-2 cursor-pointer text-sm text-gray-600">
            <input type="checkbox" v-model="showArchived" @change="loadSites" class="rounded" />
            Показать архивные
          </label>
        </div>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="s in sites" :key="s.id"
          class="card hover:shadow-md transition-shadow flex flex-col"
          :class="{ 'opacity-50 bg-gray-50': s.is_archived }"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center">
              <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                <Building2 class="w-5 h-5 text-green-600" />
              </div>
              <div>
                <h3 class="font-semibold text-gray-900">{{ s.title }}</h3>
                <p v-if="s.client_name" class="text-sm text-gray-500">{{ s.client_name }}</p>
              </div>
            </div>
            <span v-if="s.is_archived" class="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">Архив</span>
          </div>

          <div class="flex items-start text-sm text-gray-600 mb-2">
            <MapPin class="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />{{ s.address }}
          </div>
          <div v-if="s.onsite_contact" class="flex items-center text-sm text-gray-600 mb-2">
            <Phone class="w-4 h-4 mr-2" />{{ s.onsite_contact }}
          </div>
          <div v-if="s.service_frequency" class="text-sm text-gray-500 mb-2">
            Обслуживание: {{ cfg.serviceFrequencyLabel(s.service_frequency) }}
          </div>
          <div class="text-sm text-gray-500 mb-3">Выездов: {{ s.total_visits || 0 }}</div>

          <div v-if="!s.is_archived" class="flex gap-2 mt-auto pt-3 border-t">
            <button @click="openDetail(s)" class="flex-1 btn btn-secondary text-sm py-2 flex items-center justify-center">
              <Eye class="w-4 h-4 mr-1" />Подробнее
            </button>
            <button @click="openEdit(s)" class="btn btn-secondary text-sm py-2 px-3">
              <Edit class="w-4 h-4" />
            </button>
            <button @click="archiveConfirm = s" class="btn bg-amber-50 text-amber-700 hover:bg-amber-100 text-sm py-2 px-3" title="В архив">
              <Archive class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div v-if="!loading && sites.length === 0" class="text-center py-12">
        <Building2 class="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900">Объекты не найдены</h3>
      </div>

      <!-- Create/Edit Modal -->
      <div v-if="modalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">{{ editing ? 'Редактировать объект' : 'Добавить объект' }}</h2>
            <button @click="modalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleSave" class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
              <input v-model="form.title" required class="input" placeholder="Котельная №1" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Адрес *</label>
              <input v-model="form.address" required class="input" placeholder="г. Москва, ул. Ленина, д. 1" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Клиент</label>
              <select v-model="form.client_id" class="input">
                <option value="">Не выбран</option>
                <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div><label class="block text-sm font-medium text-gray-700 mb-1">Широта</label><input v-model="form.latitude" type="number" step="any" class="input" placeholder="55.751244" /></div>
              <div><label class="block text-sm font-medium text-gray-700 mb-1">Долгота</label><input v-model="form.longitude" type="number" step="any" class="input" placeholder="37.618423" /></div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Контакт на месте</label>
              <input v-model="form.onsite_contact" class="input" placeholder="Иванов И.И., тел. 8-999-000-00-00" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Доступ</label>
              <textarea v-model="form.access_notes" class="input" rows="2" placeholder="Ключ у охранника, код домофона..." />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Частота обслуживания</label>
              <select v-model="form.service_frequency" class="input">
                <option value="">Не указано</option>
                <option v-for="f in cfg.serviceFrequencies" :key="f.sysname" :value="f.sysname">{{ f.display_name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Стоимость выездов (руб.)</label>
              <div class="grid grid-cols-3 gap-3">
                <div><label class="block text-xs text-gray-500 mb-1">ТО</label><input v-model="form.price_maintenance" type="number" step="any" min="0" class="input" placeholder="0" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">Ремонт</label><input v-model="form.price_repair" type="number" step="any" min="0" class="input" placeholder="0" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">Аварийный</label><input v-model="form.price_emergency" type="number" step="any" min="0" class="input" placeholder="0" /></div>
              </div>
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
          <p class="text-gray-600 mb-1">Объект <strong>{{ archiveConfirm.title }}</strong> будет скрыт из основного списка.</p>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Plus, MapPin, Building2, Phone, X, Eye, Edit, Archive } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { useConfigStore } from '../stores/config.js'
import { useAuthStore } from '../stores/auth.js'
import { sitesAPI, clientsAPI } from '../services/api.js'

const cfg = useConfigStore()
const auth = useAuthStore()
const router = useRouter()
const sites = ref([])
const clients = ref([])
const loading = ref(true)
const search = ref('')
const showArchived = ref(false)
const modalOpen = ref(false)
const editing = ref(null)
const archiveConfirm = ref(null)
const saving = ref(false)
const form = ref({ title: '', address: '', client_id: '', latitude: '', longitude: '', onsite_contact: '', access_notes: '', service_frequency: 'monthly', price_maintenance: '', price_repair: '', price_emergency: '' })

async function loadSites() {
  loading.value = true
  try {
    const res = await sitesAPI.getAll({
      search: search.value || undefined,
      active_only: true,
      show_archived: showArchived.value || undefined,
    })
    sites.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadClients() {
  const res = await clientsAPI.getAll({ active_only: true })
  clients.value = res.data
}

function openCreate() {
  editing.value = null
  form.value = { title: '', address: '', client_id: '', latitude: '', longitude: '', onsite_contact: '', access_notes: '', service_frequency: 'monthly', price_maintenance: '', price_repair: '', price_emergency: '' }
  modalOpen.value = true
}

function openEdit(s) {
  editing.value = s
  form.value = { title: s.title, address: s.address, client_id: s.client_id || '', latitude: s.latitude || '', longitude: s.longitude || '', onsite_contact: s.onsite_contact || '', access_notes: s.access_notes || '', service_frequency: s.service_frequency || 'monthly', price_maintenance: s.price_maintenance || '', price_repair: s.price_repair || '', price_emergency: s.price_emergency || '' }
  modalOpen.value = true
}

function openDetail(s) {
  router.push(`/sites/${s.id}`)
}

async function handleSave() {
  saving.value = true
  try {
    const payload = { ...form.value, client_id: form.value.client_id || null, latitude: form.value.latitude || null, longitude: form.value.longitude || null, price_maintenance: form.value.price_maintenance || null, price_repair: form.value.price_repair || null, price_emergency: form.value.price_emergency || null }
    if (editing.value) {
      await sitesAPI.update(editing.value.id, payload)
    } else {
      await sitesAPI.create(payload)
    }
    modalOpen.value = false
    await loadSites()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function handleArchive() {
  try {
    await sitesAPI.archive(archiveConfirm.value.id)
    archiveConfirm.value = null
    await loadSites()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(() => { loadSites(); loadClients() })
</script>
