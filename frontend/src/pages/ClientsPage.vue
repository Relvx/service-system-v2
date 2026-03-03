<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Клиенты</h1>
          <p class="text-gray-600 mt-1">Всего клиентов: {{ clients.length }}</p>
        </div>
        <button @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-5 h-5 mr-2" />Добавить клиента
        </button>
      </div>

      <div class="card mb-6">
        <div class="flex gap-4 flex-wrap">
          <div class="flex-1 relative min-w-[200px]">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              v-model="search"
              @keyup.enter="loadClients"
              type="text"
              placeholder="Поиск по названию, ИНН, контактному лицу..."
              class="input pl-10"
            />
          </div>
          <button @click="loadClients" class="btn btn-primary">Найти</button>
          <label v-if="auth.hasGroup('admin_group')" class="flex items-center gap-2 cursor-pointer text-sm text-gray-600">
            <input type="checkbox" v-model="showArchived" @change="loadClients" class="rounded" />
            Показать архивные
          </label>
        </div>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="c in clients" :key="c.id"
          class="card hover:shadow-md transition-shadow flex flex-col"
          :class="{ 'opacity-50 bg-gray-50': c.is_archived }"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center">
              <div class="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center mr-3">
                <Building2 class="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <h3 class="font-semibold text-gray-900">{{ c.name }}</h3>
                <p v-if="c.inn" class="text-sm text-gray-500">ИНН: {{ c.inn }}</p>
              </div>
            </div>
            <span v-if="c.is_archived" class="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">Архив</span>
          </div>

          <div v-if="c.contact_person" class="flex items-center text-sm text-gray-600 mb-2">
            <Phone class="w-4 h-4 mr-2" />{{ c.contact_person }}
          </div>
          <div v-if="c.contacts" class="flex items-center text-sm text-gray-600 mb-3">
            <Mail class="w-4 h-4 mr-2" />{{ c.contacts.split(',')[0] }}
          </div>
          <p v-if="c.notes" class="text-sm text-gray-500 mb-3 border-t pt-3">{{ c.notes }}</p>

          <div v-if="!c.is_archived" class="flex gap-2 mt-auto pt-3 border-t">
            <router-link :to="`/clients/${c.id}`" class="flex-1 btn btn-secondary text-sm py-2 flex items-center justify-center">
              <Eye class="w-4 h-4 mr-1" />Подробнее
            </router-link>
            <button @click="openEdit(c)" class="btn btn-secondary text-sm py-2 px-3">
              <Edit class="w-4 h-4" />
            </button>
            <button @click="archiveConfirm = c" class="btn bg-amber-50 text-amber-700 hover:bg-amber-100 text-sm py-2 px-3" title="В архив">
              <Archive class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div v-if="!loading && clients.length === 0" class="text-center py-12">
        <Building2 class="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">Клиенты не найдены</h3>
      </div>

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
              <input v-model="form.name" required class="input" placeholder='ООО "Название"' />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">ИНН</label>
                <input v-model="form.inn" class="input" placeholder="1234567890" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">КПП</label>
                <input v-model="form.kpp" class="input" placeholder="123456789" />
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
import { ref, onMounted } from 'vue'
import { Search, Plus, Building2, Phone, Mail, Edit, Archive, X, Eye } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { clientsAPI } from '../services/api.js'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const clients = ref([])
const loading = ref(true)
const search = ref('')
const showArchived = ref(false)
const modalOpen = ref(false)
const editing = ref(null)
const archiveConfirm = ref(null)
const saving = ref(false)
const form = ref({ name: '', inn: '', kpp: '', contact_person: '', contacts: '', notes: '' })

async function loadClients() {
  loading.value = true
  try {
    const res = await clientsAPI.getAll({
      search: search.value || undefined,
      active_only: true,
      show_archived: showArchived.value || undefined,
    })
    clients.value = res.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.value = { name: '', inn: '', kpp: '', contact_person: '', contacts: '', notes: '' }
  modalOpen.value = true
}

function openEdit(c) {
  editing.value = c
  form.value = { name: c.name, inn: c.inn || '', kpp: c.kpp || '', contact_person: c.contact_person || '', contacts: c.contacts || '', notes: c.notes || '' }
  modalOpen.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editing.value) {
      await clientsAPI.update(editing.value.id, form.value)
    } else {
      await clientsAPI.create(form.value)
    }
    modalOpen.value = false
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

onMounted(loadClients)
</script>
