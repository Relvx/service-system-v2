<template>
  <Layout>
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>

    <div v-else-if="client">
      <!-- Шапка -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <button @click="$router.back()" class="text-gray-500 hover:text-gray-700">
            <ArrowLeft class="w-5 h-5" />
          </button>
          <div>
            <h1 class="text-3xl font-bold text-gray-900">{{ client.name }}</h1>
            <p v-if="client.inn" class="text-gray-500 mt-0.5 text-sm">ИНН: {{ client.inn }}<span v-if="client.kpp"> / КПП: {{ client.kpp }}</span></p>
          </div>
          <span v-if="client.is_archived" class="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">Архив</span>
        </div>
        <button v-if="!client.is_archived" @click="openEdit" class="btn btn-secondary flex items-center">
          <Edit class="w-4 h-4 mr-2" />Редактировать
        </button>
      </div>

      <!-- Вкладки -->
      <div class="border-b mb-6">
        <nav class="flex gap-6">
          <button
            v-for="tab in tabs" :key="tab.key"
            @click="activeTab = tab.key"
            class="pb-3 text-sm font-medium border-b-2 transition-colors"
            :class="activeTab === tab.key
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'"
          >
            {{ tab.label }}
            <span v-if="tab.count !== undefined" class="ml-1 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">{{ tab.count }}</span>
          </button>
        </nav>
      </div>

      <!-- Основное -->
      <div v-if="activeTab === 'main'" class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="card space-y-4">
          <h3 class="font-semibold text-gray-900">Основная информация</h3>
          <div><p class="text-sm text-gray-500">Название</p><p class="text-gray-900">{{ client.name }}</p></div>
          <div v-if="client.inn"><p class="text-sm text-gray-500">ИНН</p><p class="text-gray-900">{{ client.inn }}</p></div>
          <div v-if="client.kpp"><p class="text-sm text-gray-500">КПП</p><p class="text-gray-900">{{ client.kpp }}</p></div>
          <div v-if="client.contact_person"><p class="text-sm text-gray-500">Контактное лицо</p><p class="text-gray-900">{{ client.contact_person }}</p></div>
          <div v-if="client.contacts"><p class="text-sm text-gray-500">Контакты</p><p class="text-gray-900">{{ client.contacts }}</p></div>
          <div v-if="client.notes"><p class="text-sm text-gray-500">Заметки</p><p class="text-gray-900 whitespace-pre-wrap">{{ client.notes }}</p></div>
        </div>

        <div class="card space-y-4">
          <h3 class="font-semibold text-gray-900">Юридические реквизиты</h3>
          <div v-if="client.legal">
            <div v-if="client.legal.legal_address"><p class="text-sm text-gray-500">Юр. адрес</p><p class="text-gray-900">{{ client.legal.legal_address }}</p></div>
            <div v-if="client.legal.bank" class="mt-3"><p class="text-sm text-gray-500">Банк</p><p class="text-gray-900">{{ client.legal.bank }}</p></div>
            <div v-if="client.legal.bik" class="mt-3"><p class="text-sm text-gray-500">БИК</p><p class="text-gray-900">{{ client.legal.bik }}</p></div>
            <div v-if="client.legal.account" class="mt-3"><p class="text-sm text-gray-500">Р/С</p><p class="text-gray-900">{{ client.legal.account }}</p></div>
          </div>
          <p v-else class="text-sm text-gray-400">Реквизиты не заполнены</p>
          <button @click="openLegalModal" class="btn btn-secondary text-sm">
            {{ client.legal ? 'Редактировать реквизиты' : 'Добавить реквизиты' }}
          </button>
        </div>
      </div>

      <!-- Контакты -->
      <div v-if="activeTab === 'contacts'">
        <div class="flex justify-end mb-4">
          <button @click="openContactCreate" class="btn btn-primary flex items-center">
            <Plus class="w-4 h-4 mr-2" />Добавить контакт
          </button>
        </div>
        <div v-if="client.contact_persons.length === 0" class="text-center py-12 card">
          <User class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-gray-500">Контактные лица не добавлены</p>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="c in client.contact_persons" :key="c.id" class="card">
            <div class="flex items-start justify-between mb-2">
              <div>
                <p class="font-semibold text-gray-900">{{ c.full_name }}</p>
                <p v-if="c.position" class="text-sm text-gray-500">{{ c.position }}</p>
              </div>
              <span v-if="c.is_primary" class="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">Основной</span>
            </div>
            <div v-if="c.phone" class="flex items-center text-sm text-gray-600 mb-1"><Phone class="w-4 h-4 mr-2" />{{ c.phone }}</div>
            <div v-if="c.email" class="flex items-center text-sm text-gray-600 mb-3"><Mail class="w-4 h-4 mr-2" />{{ c.email }}</div>
            <div class="flex gap-2 border-t pt-3">
              <button @click="openContactEdit(c)" class="flex-1 btn btn-secondary text-sm py-1.5 flex items-center justify-center">
                <Edit class="w-3.5 h-3.5 mr-1" />Изменить
              </button>
              <button @click="contactDeleteConfirm = c" class="btn bg-red-50 text-red-600 hover:bg-red-100 text-sm py-1.5 px-3">
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Объекты -->
      <div v-if="activeTab === 'sites'">
        <div v-if="client.sites.length === 0" class="text-center py-12 card">
          <Building2 class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-gray-500">Объекты не найдены</p>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <router-link
            v-for="s in client.sites" :key="s.id"
            :to="`/sites/${s.id}`"
            class="card hover:shadow-md transition-shadow block"
          >
            <div class="flex items-center mb-2">
              <div class="w-9 h-9 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                <Building2 class="w-4 h-4 text-green-600" />
              </div>
              <div>
                <p class="font-semibold text-gray-900 text-sm">{{ s.title }}</p>
                <p v-if="s.service_frequency" class="text-xs text-gray-500">{{ cfg.serviceFrequencyLabel(s.service_frequency) }}</p>
              </div>
            </div>
            <div class="flex items-start text-sm text-gray-600">
              <MapPin class="w-4 h-4 mr-1.5 mt-0.5 flex-shrink-0" />{{ s.address }}
            </div>
          </router-link>
        </div>
      </div>

      <!-- Файлы -->
      <div v-if="activeTab === 'files'">
        <AttachmentsTab entity-type="client" :entity-id="client.id" />
      </div>

      <!-- История выездов -->
      <div v-if="activeTab === 'visits'">
        <div v-if="client.recent_visits.length === 0" class="text-center py-12 card">
          <Calendar class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-gray-500">Выездов не найдено</p>
        </div>
        <div v-else class="space-y-3">
          <div v-for="v in client.recent_visits" :key="v.id" class="card">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <p class="font-medium text-gray-900">{{ v.site_title }}</p>
                <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="statusClass(v.status)">
                  {{ cfg.visitStatusLabel(v.status) }}
                </span>
                <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="priorityClass(v.priority)">
                  {{ cfg.priorityLabel(v.priority) }}
                </span>
              </div>
              <div class="flex items-center gap-4 text-sm text-gray-500">
                <span>{{ formatDate(v.planned_date) }}</span>
                <span v-if="v.master_name">{{ v.master_name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Client Modal -->
    <div v-if="editModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
        <div class="flex items-center justify-between p-6 border-b">
          <h2 class="text-xl font-semibold text-gray-900">Редактировать клиента</h2>
          <button @click="editModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleEditSave" class="p-6 space-y-4">
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Название *</label><input v-model="editForm.name" required class="input" /></div>
          <div class="grid grid-cols-2 gap-4">
            <div><label class="block text-sm font-medium text-gray-700 mb-1">ИНН</label><input v-model="editForm.inn" class="input" /></div>
            <div><label class="block text-sm font-medium text-gray-700 mb-1">КПП</label><input v-model="editForm.kpp" class="input" /></div>
          </div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Контактное лицо</label><input v-model="editForm.contact_person" class="input" /></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Контакты</label><input v-model="editForm.contacts" class="input" /></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label><textarea v-model="editForm.notes" class="input" rows="3" /></div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="editModalOpen = false" class="btn btn-secondary">Отмена</button>
            <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Legal Modal -->
    <div v-if="legalModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
        <div class="flex items-center justify-between p-6 border-b">
          <h2 class="text-xl font-semibold text-gray-900">Юридические реквизиты</h2>
          <button @click="legalModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleLegalSave" class="p-6 space-y-4">
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Юридический адрес</label><textarea v-model="legalForm.legal_address" class="input" rows="2" /></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Банк</label><input v-model="legalForm.bank" class="input" placeholder="ПАО Сбербанк" /></div>
          <div class="grid grid-cols-2 gap-4">
            <div><label class="block text-sm font-medium text-gray-700 mb-1">БИК</label><input v-model="legalForm.bik" class="input" placeholder="044525225" /></div>
            <div><label class="block text-sm font-medium text-gray-700 mb-1">Расчётный счёт</label><input v-model="legalForm.account" class="input" placeholder="40702810..." /></div>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="legalModalOpen = false" class="btn btn-secondary">Отмена</button>
            <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Contact Create/Edit Modal -->
    <div v-if="contactModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div class="flex items-center justify-between p-6 border-b">
          <h2 class="text-xl font-semibold text-gray-900">{{ editingContact ? 'Редактировать контакт' : 'Добавить контакт' }}</h2>
          <button @click="contactModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleContactSave" class="p-6 space-y-4">
          <div><label class="block text-sm font-medium text-gray-700 mb-1">ФИО *</label><input v-model="contactForm.full_name" required class="input" placeholder="Иванов Иван Иванович" /></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Должность</label><input v-model="contactForm.position" class="input" placeholder="Директор" /></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Телефон</label><input v-model="contactForm.phone" class="input" placeholder="+7-900-000-00-00" /></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Email</label><input v-model="contactForm.email" type="email" class="input" placeholder="ivan@company.ru" /></div>
          <label class="flex items-center gap-2 cursor-pointer text-sm text-gray-700">
            <input type="checkbox" v-model="contactForm.is_primary" class="rounded" />
            Основной контакт
          </label>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="contactModalOpen = false" class="btn btn-secondary">Отмена</button>
            <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">{{ saving ? 'Сохранение...' : (editingContact ? 'Сохранить' : 'Добавить') }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Contact Delete Confirm -->
    <div v-if="contactDeleteConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Удалить контакт?</h2>
        <p class="text-gray-600 mb-6">Контакт <strong>{{ contactDeleteConfirm.full_name }}</strong> будет удалён.</p>
        <div class="flex justify-end gap-3">
          <button @click="contactDeleteConfirm = null" class="btn btn-secondary">Отмена</button>
          <button @click="handleContactDelete" class="btn bg-red-600 text-white hover:bg-red-700">Удалить</button>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Edit, Plus, X, Phone, Mail, Building2, MapPin, Calendar, User, Trash2 } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import AttachmentsTab from '../components/AttachmentsTab.vue'
import { useConfigStore } from '../stores/config.js'
import { clientsAPI } from '../services/api.js'

const route = useRoute()
const cfg = useConfigStore()

const client = ref(null)
const loading = ref(true)
const activeTab = ref('main')
const saving = ref(false)

// Edit client
const editModalOpen = ref(false)
const editForm = ref({})

// Legal
const legalModalOpen = ref(false)
const legalForm = ref({ legal_address: '', bank: '', bik: '', account: '' })

// Contacts
const contactModalOpen = ref(false)
const editingContact = ref(null)
const contactDeleteConfirm = ref(null)
const contactForm = ref({ full_name: '', position: '', phone: '', email: '', is_primary: false })

const tabs = computed(() => [
  { key: 'main', label: 'Основное' },
  { key: 'contacts', label: 'Контакты', count: client.value?.contact_persons?.length ?? 0 },
  { key: 'sites', label: 'Объекты', count: client.value?.sites?.length ?? 0 },
  { key: 'visits', label: 'История выездов', count: client.value?.recent_visits?.length ?? 0 },
  { key: 'files', label: 'Файлы и фото' },
])

async function loadClient() {
  loading.value = true
  try {
    const res = await clientsAPI.getById(route.params.id)
    client.value = res.data
  } finally {
    loading.value = false
  }
}

function openEdit() {
  editForm.value = {
    name: client.value.name,
    inn: client.value.inn || '',
    kpp: client.value.kpp || '',
    contact_person: client.value.contact_person || '',
    contacts: client.value.contacts || '',
    notes: client.value.notes || '',
  }
  editModalOpen.value = true
}

async function handleEditSave() {
  saving.value = true
  try {
    await clientsAPI.update(client.value.id, editForm.value)
    editModalOpen.value = false
    await loadClient()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function openLegalModal() {
  legalForm.value = {
    legal_address: client.value.legal?.legal_address || '',
    bank: client.value.legal?.bank || '',
    bik: client.value.legal?.bik || '',
    account: client.value.legal?.account || '',
  }
  legalModalOpen.value = true
}

async function handleLegalSave() {
  saving.value = true
  try {
    await clientsAPI.upsertLegal(client.value.id, legalForm.value)
    legalModalOpen.value = false
    await loadClient()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function openContactCreate() {
  editingContact.value = null
  contactForm.value = { full_name: '', position: '', phone: '', email: '', is_primary: false }
  contactModalOpen.value = true
}

function openContactEdit(c) {
  editingContact.value = c
  contactForm.value = { full_name: c.full_name, position: c.position || '', phone: c.phone || '', email: c.email || '', is_primary: c.is_primary }
  contactModalOpen.value = true
}

async function handleContactSave() {
  saving.value = true
  try {
    if (editingContact.value) {
      await clientsAPI.updateContact(client.value.id, editingContact.value.id, contactForm.value)
    } else {
      await clientsAPI.addContact(client.value.id, contactForm.value)
    }
    contactModalOpen.value = false
    await loadClient()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function handleContactDelete() {
  try {
    await clientsAPI.deleteContact(client.value.id, contactDeleteConfirm.value.id)
    contactDeleteConfirm.value = null
    await loadClient()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

function statusClass(s) {
  const m = { planned: 'bg-blue-100 text-blue-700', in_progress: 'bg-green-100 text-green-700', closed: 'bg-gray-400 text-white', done: 'bg-gray-400 text-white', cancelled: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-700'
}
function priorityClass(p) {
  const m = { low: 'bg-gray-100 text-gray-600', medium: 'bg-yellow-100 text-yellow-700', high: 'bg-orange-100 text-orange-700', urgent: 'bg-red-100 text-red-700' }
  return m[p] || 'bg-gray-100 text-gray-700'
}
function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }

onMounted(loadClient)
</script>
