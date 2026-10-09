<template>
  <Layout>
    <div class="space-y-5">
      <header class="flex flex-wrap justify-between items-start gap-3">
        <div><h1 class="text-2xl md:text-3xl font-bold">Заявки с сайта</h1><p class="text-gray-600 mt-1">Обращения до создания клиента и планирования выезда · Всего: {{ total }}</p></div>
        <button v-if="auth.hasGroup('admin_group')" class="btn btn-secondary" @click="toggleConnections">Подключение сайта</button>
      </header>
      <section v-if="connectionsOpen" class="card space-y-3">
        <div class="flex justify-between gap-3"><h2 class="font-semibold">Доступ только для приёма заявок</h2><button class="text-primary-600" @click="closeConnections">Закрыть</button></div>
        <p class="text-sm text-gray-600">Ключ используется сервером сайта. Он не открывает клиентов и отчёты. При замене сначала подключите новый ключ, затем отзовите старый.</p>
        <form class="flex flex-wrap items-end gap-3" @submit.prevent="newConnection">
          <label class="text-sm">Название<input v-model="connectionForm.label" required maxlength="100" class="input mt-1" /></label>
          <label class="text-sm">Срок, дней<input v-model.number="connectionForm.expires_days" type="number" required min="1" max="365" class="input mt-1 w-28" /></label>
          <button :disabled="busy" class="btn btn-primary">Создать ключ</button>
        </form>
        <div v-if="secret" class="bg-amber-50 p-3 rounded space-y-2">
          <label class="text-sm block">Сохраните ключ сейчас: повторно он не показывается.<textarea readonly :value="secret" class="input mt-2 font-mono break-all" aria-label="Новый ключ подключения" /></label>
          <button class="btn btn-secondary text-sm" @click="copySecret">Копировать ключ</button>
          <p class="text-sm">{{ copyNotice }}</p>
        </div>
        <p v-if="connectionError" role="alert" class="text-red-700">{{ connectionError }}</p>
        <div v-for="c in connections" :key="c.id" class="flex justify-between flex-wrap gap-3 border-t pt-3 text-sm">
          <span>{{ c.label }} · до {{ dateLabel(c.expires_at) }} · {{ c.revoked ? 'Отозван' : new Date(c.expires_at) <= new Date() ? 'Истёк' : 'Активен' }}</span>
          <button v-if="!c.revoked" :disabled="busy" class="text-red-700 underline" @click="revoke(c)">Отозвать</button>
        </div>
      </section>
      <form class="card flex flex-wrap items-end gap-3" @submit.prevent="applyFilters">
        <label class="text-sm">Поиск<input v-model="filters.q" class="input mt-1" maxlength="200" placeholder="Номер, телефон, клиент" /></label>
        <label class="text-sm">Статус<select v-model="filters.status" class="input mt-1"><option value="">Все</option><option v-for="(label, value) in statuses" :key="value" :value="value">{{ label }}</option></select></label>
        <label class="text-sm">Ответственный<select v-model="filters.assigned_user_id" class="input mt-1"><option value="">Все</option><option value="0">Не назначен</option><option v-for="u in assignees" :key="u.id" :value="u.id">{{ u.full_name }}</option></select></label>
        <label class="text-sm">Направление<select v-model="filters.service_category" class="input mt-1"><option value="">Все</option><option v-for="(label, value) in categories" :key="value" :value="value">{{ label }}</option></select></label>
        <label class="text-sm">С даты<input v-model="filters.date_from" type="date" class="input mt-1" /></label>
        <label class="text-sm">По дату<input v-model="filters.date_to" type="date" class="input mt-1" /></label>
        <button class="btn btn-primary" :disabled="loading">Показать</button>
      </form>
      <p v-if="error" role="alert" class="bg-red-50 text-red-700 p-3 rounded">{{ error }}</p>
      <p v-if="loading" role="status">Загружаю заявки…</p>
      <DataTable :columns="columns" :rows="rows" :total="total" :page="page" :page-size="pageSize" :loading="loading" storage-key="website-request-columns" @row-click="open" @update:page="changePage" @update:page-size="changePageSize" @reload="load">
        <template #website_reference="{ row }"><router-link :to="`/website-requests/${row.id}`" class="text-primary-600 font-medium underline">{{ row.website_reference }}</router-link><p class="text-xs text-gray-500 mt-1">{{ row.request_mode === 'callback' ? 'Перезвонить' : 'Подробная заявка' }}</p></template>
        <template #received_at="{ row }">{{ dateLabel(row.received_at) }}</template>
        <template #client="{ row }"><span class="block truncate">{{ row.company_name || row.contact_name || 'Новый контакт' }}</span><span v-if="row.request_intent !== 'general'" class="text-xs text-primary-600">{{ intents[row.request_intent] }}</span></template>
        <template #service_category="{ row }"><span>{{ categories[row.service_category] || 'Нужно уточнить' }}</span><p class="text-xs mt-1" :class="row.work_type === 'emergency' ? 'text-red-700 font-medium' : 'text-gray-500'">{{ workTypes[row.work_type] || '' }}</p></template>
        <template #status="{ row }"><span class="rounded px-2 py-1 text-xs" :class="row.status === 'new' ? 'bg-blue-50 text-blue-700' : row.status === 'in_progress' ? 'bg-amber-50 text-amber-800' : 'bg-gray-100 text-gray-700'">{{ statuses[row.status] }}</span></template>
        <template #assigned_name="{ row }">{{ row.assigned_name || 'Не назначен' }}</template>
        <template #empty>Заявок по выбранным условиям нет.</template>
      </DataTable>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import { websiteRequestsAPI as api } from '../services/api.js'
import { useAuthStore } from '../stores/auth.js'
import { statuses, categories, workTypes, intents, dateLabel, errorMessage } from '../utils/websiteRequests.js'
const auth = useAuthStore(), router = useRouter()
const rows = ref([]), total = ref(0), page = ref(1), pageSize = ref(50), loading = ref(false), error = ref(''), assignees = ref([])
const filters = ref({ q: '', status: '', assigned_user_id: '', service_category: '', date_from: '', date_to: '' })
let appliedFilters = {}, loadVersion = 0
const columns = [
  { key: 'website_reference', label: 'Заявка', width: 170 }, { key: 'received_at', label: 'Получена', width: 150 },
  { key: 'client', label: 'Клиент', width: 230 }, { key: 'phone', label: 'Телефон', width: 155 },
  { key: 'service_category', label: 'Работы', width: 200 }, { key: 'status', label: 'Статус', width: 120 },
  { key: 'assigned_name', label: 'Ответственный', width: 185 },
].map(c => ({ ...c, sortable: false }))
const connectionsOpen = ref(false), connections = ref([]), busy = ref(false), secret = ref(''), connectionError = ref(''), copyNotice = ref('')
const connectionForm = ref({ label: 'Сайт Аналит-ГАЗ', expires_days: 90 })
async function load() {
  const version = ++loadVersion
  loading.value = true; error.value = ''
  try { const { data } = await api.getAll({ ...appliedFilters, limit: pageSize.value, offset: (page.value - 1) * pageSize.value }); if (version === loadVersion) { rows.value = data.items; total.value = data.total } }
  catch (e) { if (version === loadVersion) error.value = errorMessage(e) }
  finally { if (version === loadVersion) loading.value = false }
}
function applyFilters() { appliedFilters = Object.fromEntries(Object.entries(filters.value).filter(([, v]) => v !== '')); page.value = 1; load() }
function changePage(value) { page.value = value; load() }
function changePageSize(value) { pageSize.value = value; page.value = 1; load() }
function open(row) { router.push(`/website-requests/${row.id}`) }
function closeConnections() { connectionsOpen.value = false; secret.value = ''; copyNotice.value = '' }
async function toggleConnections() {
  if (connectionsOpen.value) { closeConnections(); return }
  connectionsOpen.value = true; connectionError.value = ''
  try { connections.value = (await api.connections()).data } catch (e) { connectionError.value = errorMessage(e) }
}
async function newConnection() {
  if (busy.value) return
  busy.value = true; connectionError.value = ''; secret.value = ''; copyNotice.value = ''
  try { const { data } = await api.connect(connectionForm.value); secret.value = data.token; connections.value = (await api.connections()).data }
  catch (e) { connectionError.value = errorMessage(e) } finally { busy.value = false }
}
async function copySecret() {
  try { await navigator.clipboard.writeText(secret.value); copyNotice.value = 'Ключ скопирован.' }
  catch { copyNotice.value = 'Выделите и скопируйте ключ из поля вручную.' }
}
async function revoke(c) {
  if (busy.value || !window.confirm(`Отозвать подключение «${c.label}»? Если сайт использует этот ключ, передача остановится до его замены.`)) return
  busy.value = true
  try { await api.revoke(c.id); connections.value = (await api.connections()).data; secret.value = '' }
  catch (e) { connectionError.value = errorMessage(e) } finally { busy.value = false }
}
onMounted(async () => { await load(); try { assignees.value = (await api.assignees()).data } catch (e) { error.value = errorMessage(e) } })
</script>
