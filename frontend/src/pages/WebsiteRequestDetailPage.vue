<template>
  <Layout>
    <div class="space-y-5">
      <router-link to="/website-requests" class="text-primary-600 underline">← Заявки с сайта</router-link>
      <p v-if="error" role="alert" class="bg-red-50 text-red-700 p-3 rounded">{{ error }} <button class="underline ml-2" :disabled="busy" @click="load">Обновить карточку</button></p>
      <p v-if="notice" role="status" class="bg-green-50 text-green-800 p-3 rounded">{{ notice }}</p>
      <p v-if="loading">Загружаю обращение…</p>
      <template v-if="request">
        <header class="flex justify-between items-start flex-wrap gap-3">
          <div><h1 class="text-2xl md:text-3xl font-bold">{{ request.website_reference }}</h1><p class="text-gray-600 mt-1">{{ request.request_mode === 'callback' ? 'Просьба перезвонить' : 'Подробная заявка' }} · {{ dateLabel(request.received_at) }} МСК</p><p v-if="request.request_intent !== 'general'" class="text-primary-600 mt-1">{{ intents[request.request_intent] }}</p></div>
          <button v-if="['new', 'in_progress'].includes(request.status) && request.assigned_user_id !== auth.user?.id" class="btn btn-primary" :disabled="busy" @click="take">Взять в работу</button>
        </header>
        <div class="grid lg:grid-cols-2 gap-5">
          <section class="card space-y-4">
            <div><h2 class="font-semibold text-lg">Исходное обращение</h2><p class="text-sm text-gray-500">Данные посетителя сохраняются без изменений.</p></div>
            <dl class="grid grid-cols-1 sm:grid-cols-[150px_1fr] gap-x-4 gap-y-3 text-sm">
              <template v-for="[label, value] in originalFields" :key="label"><dt class="text-gray-500">{{ label }}</dt><dd class="whitespace-pre-wrap break-words">{{ value || 'Не указано' }}</dd></template>
            </dl>
            <p v-if="request.payload.work_type === 'emergency'" class="bg-amber-50 text-amber-800 p-3 rounded text-sm">Запрошен аварийный выезд. Уточните ситуацию и возможность выезда при связи с клиентом.</p>
            <details class="text-sm border-t pt-3"><summary class="cursor-pointer text-gray-600">Источник и согласие</summary><dl class="mt-3 space-y-2"><div>Страница: {{ request.payload.source_page }}</div><div>Отправлено: {{ dateLabel(request.payload.submitted_at) }} МСК</div><div>Согласие: {{ dateLabel(request.payload.consent.accepted_at) }} МСК · {{ request.payload.consent.policy_version }}</div><div class="break-all">Внешний ID: {{ request.external_id }}</div></dl></details>
          </section>
          <form class="card space-y-4" @submit.prevent="save">
            <h2 class="font-semibold text-lg">Работа с обращением</h2>
            <fieldset :disabled="busy" class="space-y-4">
              <div class="grid sm:grid-cols-2 gap-3"><label class="text-sm">Статус<select v-model="draft.status" class="input mt-1"><option v-for="(label, value) in statuses" :key="value" :value="value">{{ label }}</option></select></label><label class="text-sm">Ответственный<select v-model="draft.assigned_user_id" class="input mt-1"><option :value="null">Не назначен</option><option v-for="u in assignees" :key="u.id" :value="u.id">{{ u.full_name }}</option></select></label></div>
              <p v-if="request.assigned_user_id && !assignees.some(u => u.id === request.assigned_user_id)" class="text-amber-800 text-sm">Прежний ответственный недоступен. Выберите активного сотрудника.</p>
              <div class="grid sm:grid-cols-2 gap-3"><label v-for="f in workingFields.filter(f => f.key !== 'message')" :key="f.key" class="text-sm">{{ f.label }}<input v-model="draft.working_data[f.key]" :type="f.key === 'email' ? 'email' : f.key === 'phone' ? 'tel' : 'text'" :maxlength="f.max" class="input mt-1" /></label></div>
              <label class="text-sm block">Уточнённая задача<textarea v-model="draft.working_data.message" maxlength="3000" rows="3" class="input mt-1" /></label>
              <label class="text-sm block">Итог обращения <span v-if="draft.status === 'closed'" class="text-red-600">*</span><textarea v-model="draft.outcome" :required="draft.status === 'closed'" maxlength="2000" rows="2" class="input mt-1" placeholder="Что согласовали с клиентом" /></label>
              <button class="btn btn-primary">{{ busy ? 'Сохраняю…' : 'Сохранить изменения' }}</button>
            </fieldset>
          </form>
        </div>
        <section class="card space-y-4">
          <div class="flex justify-between flex-wrap gap-3"><div><h2 class="font-semibold text-lg">Клиент и объект</h2><p class="text-sm text-gray-500">Связывайте записи после уточнения данных. Выезд и договор оформляются отдельно.</p></div><button class="btn btn-secondary" :disabled="busy" @click="openLink">{{ request.client_id ? 'Изменить связи' : 'Связать или создать' }}</button></div>
          <div class="flex flex-wrap gap-5 text-sm"><router-link v-if="request.links.client" :to="`/clients/${request.client_id}`" class="text-primary-600 underline">{{ request.links.client.name }}</router-link><router-link v-if="request.links.site" :to="`/sites/${request.site_id}`" class="text-primary-600 underline">{{ request.links.site.name }}</router-link><span v-if="request.links.contact">Контакт: {{ request.links.contact.name }}</span><span v-if="!request.client_id" class="text-gray-500">Пока не связано со справочниками</span></div>
          <form v-if="linkOpen" class="border-t pt-4 space-y-4" @submit.prevent="saveLink">
            <fieldset :disabled="busy" class="space-y-4">
              <div class="flex gap-4 flex-wrap text-sm"><label><input v-model="linkForm.client_mode" type="radio" value="existing" @change="clearSelection" /> Существующий клиент</label><label v-if="!request.client_id"><input v-model="linkForm.client_mode" type="radio" value="new" @change="clearSelection" /> Новый клиент</label></div>
              <template v-if="linkForm.client_mode === 'existing'">
                <div class="flex items-end gap-3"><label class="text-sm flex-1">Найти клиента<input v-model="clientQuery" class="input mt-1" maxlength="200" /></label><button type="button" class="btn btn-secondary" :disabled="lookupBusy" @click="searchClients">Найти</button></div>
                <label class="text-sm block">Клиент<select v-model="linkForm.client_id" required class="input mt-1" @change="selectClient"><option value="">Выберите клиента</option><option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option></select></label>
                <p v-if="clientsTotal > clients.length" class="text-sm text-gray-500">Найдено {{ clientsTotal }} клиентов. Уточните поиск, если нужного нет среди первых {{ clients.length }}.</p>
              </template>
              <label v-else class="text-sm block">Название компании или ФИО клиента<input v-model="linkForm.client_name" required maxlength="300" class="input mt-1" /></label>
              <div class="grid md:grid-cols-2 gap-4">
                <section class="space-y-3"><h3 class="font-medium">Контакт</h3><select v-model="linkForm.contact_mode" class="input" aria-label="Действие с контактом"><option value="none">Без контакта</option><option v-if="linkForm.client_mode === 'existing'" value="existing">Выбрать контакт клиента</option><option value="new">Создать контакт</option></select><select v-if="linkForm.contact_mode === 'existing'" v-model="linkForm.contact_id" required class="input" aria-label="Контакт клиента"><option value="">Выберите контакт</option><option v-for="c in contacts" :key="c.id" :value="c.id">{{ c.full_name }} · {{ c.phone }}</option></select><template v-if="linkForm.contact_mode === 'new'"><label class="text-sm block">Имя<input v-model="linkForm.contact_name" required maxlength="100" class="input mt-1" /></label><label class="text-sm block">Телефон<input v-model="linkForm.phone" type="tel" maxlength="20" class="input mt-1" /></label><label class="text-sm block">Email<input v-model="linkForm.email" type="email" maxlength="254" class="input mt-1" /></label></template></section>
                <section class="space-y-3"><h3 class="font-medium">Объект</h3><select v-model="linkForm.site_mode" class="input" aria-label="Действие с объектом"><option value="none">Уточнить позднее</option><option v-if="linkForm.client_mode === 'existing'" value="existing">Выбрать объект клиента</option><option value="new">Создать объект</option></select><select v-if="linkForm.site_mode === 'existing'" v-model="linkForm.site_id" required class="input" aria-label="Объект клиента"><option value="">Выберите объект</option><option v-for="s in sites" :key="s.id" :value="s.id">{{ s.title }} · {{ s.address }}</option></select><template v-if="linkForm.site_mode === 'new'"><label class="text-sm block">Название объекта<input v-model="linkForm.site_title" required maxlength="300" class="input mt-1" /></label><label class="text-sm block">Адрес<input v-model="linkForm.site_address" required maxlength="300" class="input mt-1" /></label></template></section>
              </div>
              <div class="flex gap-3"><button class="btn btn-primary" :disabled="lookupBusy">Сохранить связи</button><button type="button" class="btn btn-secondary" @click="linkOpen = false">Отмена</button></div>
            </fieldset>
          </form>
        </section>
        <section class="card space-y-4">
          <h2 class="font-semibold text-lg">История обращения</h2>
          <form class="flex items-end gap-3" @submit.prevent="addComment"><label class="text-sm flex-1">Комментарий<textarea v-model="commentText" required maxlength="3000" rows="2" class="input mt-1" :disabled="busy" /></label><button class="btn btn-secondary" :disabled="busy || !commentText.trim()">Добавить</button></form>
          <ol class="space-y-3"><li v-for="e in request.events" :key="e.id" class="border-t pt-3 text-sm"><p class="font-medium">{{ eventLabels[e.kind] || e.kind }} <span class="font-normal text-gray-500">· {{ e.author_name || 'Удалённый сотрудник' }} · {{ dateLabel(e.created_at) }} МСК</span></p><p v-if="e.kind === 'comment'" class="whitespace-pre-wrap break-words mt-1">{{ e.data.text }}</p><p v-else class="text-gray-600 mt-1">{{ eventDescription(e) }}</p></li></ol>
        </section>
      </template>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import Layout from '../components/Layout.vue'
import { websiteRequestsAPI as api, clientsAPI } from '../services/api.js'
import { useAuthStore } from '../stores/auth.js'
import { statuses, categories, workTypes, customerTypes, formats, intents, dateLabel, errorMessage } from '../utils/websiteRequests.js'
const route = useRoute(), auth = useAuthStore()
const request = ref(null), draft = ref({}), loading = ref(false), busy = ref(false), error = ref(''), notice = ref(''), assignees = ref([]), commentText = ref('')
const linkOpen = ref(false), linkForm = ref({}), clients = ref([]), clientsTotal = ref(0), contacts = ref([]), sites = ref([]), clientQuery = ref(''), lookupBusy = ref(false)
let loadVersion = 0, lookupVersion = 0, pendingLink = null
const workingFields = [{ key: 'contact_name', label: 'Контактное лицо', max: 100 }, { key: 'company_name', label: 'Компания', max: 180 }, { key: 'phone', label: 'Телефон', max: 20 }, { key: 'email', label: 'Email', max: 254 }, { key: 'object_address', label: 'Адрес объекта', max: 300 }, { key: 'message', label: 'Задача', max: 3000 }]
const eventLabels = { received: 'Получено с сайта', updated: 'Изменено', comment: 'Комментарий', linked: 'Связано с клиентом и объектом' }
const originalFields = computed(() => {
  const p = request.value.payload
  return [['Телефон', p.phone], ['Контакт', p.contact_name], ['Компания', p.company_name], ['Тип клиента', customerTypes[p.customer_type]], ['Email', p.email], ['Оборудование', categories[p.service_category]], ['Вид работ', workTypes[p.work_type]], ['Формат', formats[p.cooperation_format]], ['Адрес', p.object_address], ['Описание', p.message], ...(p.legacy_equipment ? [['Прежняя форма: оборудование', p.legacy_equipment.description], ['Мощность', p.legacy_equipment.power]] : [])]
})
function setRequest(data) {
  if (String(data.id) !== String(route.params.id)) return
  request.value = data
  const working = {}
  for (const f of workingFields) working[f.key] = data.working_data[f.key] ?? data.payload[f.key] ?? ''
  draft.value = { status: data.status, assigned_user_id: data.assigned_user_id, working_data: working, outcome: data.outcome || '' }
}
async function load() {
  const version = ++loadVersion, id = route.params.id
  loading.value = true; error.value = ''
  try { const [r, a] = await Promise.all([api.getById(id), api.assignees()]); if (version === loadVersion) { setRequest(r.data); assignees.value = a.data; linkOpen.value = false } }
  catch (e) { if (version === loadVersion) { request.value = null; error.value = errorMessage(e) } }
  finally { if (version === loadVersion) loading.value = false }
}
async function action(fn, success) {
  if (busy.value) return
  busy.value = true; error.value = ''; notice.value = ''
  try { await fn(); notice.value = success }
  catch (e) { error.value = errorMessage(e) }
  finally { busy.value = false }
}
const nullable = value => value?.trim() || null
function save() {
  const body = { version: request.value.version, status: draft.value.status, assigned_user_id: draft.value.assigned_user_id, outcome: nullable(draft.value.outcome), working_data: Object.fromEntries(workingFields.map(f => [f.key, nullable(draft.value.working_data[f.key])])) }
  action(async () => setRequest((await api.update(request.value.id, body)).data), 'Изменения сохранены.')
}
function take() { action(async () => setRequest((await api.update(request.value.id, { version: request.value.version, assigned_user_id: auth.user.id, status: 'in_progress' })).data), 'Вы взяли заявку в работу.') }
function addComment() { action(async () => { const { data } = await api.comment(request.value.id, commentText.value); if (String(data.id) === String(route.params.id)) { request.value = data; commentText.value = '' } }, 'Комментарий добавлен.') }
async function searchClients() {
  const version = ++lookupVersion
  lookupBusy.value = true
  try { const { data } = await clientsAPI.getAll({ search: clientQuery.value.trim(), active_only: true, limit: 50 }); if (version === lookupVersion) { clients.value = data.items; clientsTotal.value = data.total } }
  catch (e) { if (version === lookupVersion) error.value = errorMessage(e) }
  finally { if (version === lookupVersion) lookupBusy.value = false }
}
function clearSelection() { ++lookupVersion; lookupBusy.value = false; linkForm.value.client_id = ''; linkForm.value.contact_id = ''; linkForm.value.site_id = ''; linkForm.value.contact_mode = 'none'; linkForm.value.site_mode = 'none'; contacts.value = []; sites.value = [] }
async function selectClient() {
  const version = ++lookupVersion
  contacts.value = []; sites.value = []; linkForm.value.contact_id = ''; linkForm.value.site_id = ''
  if (!linkForm.value.client_id) return
  lookupBusy.value = true
  try { const { data } = await clientsAPI.getById(linkForm.value.client_id); if (version === lookupVersion) { contacts.value = data.contact_persons; sites.value = data.sites.filter(s => !s.is_archived) } }
  catch (e) { if (version === lookupVersion) error.value = errorMessage(e) }
  finally { if (version === lookupVersion) lookupBusy.value = false }
}
async function openLink() {
  error.value = ''; linkOpen.value = true
  const r = request.value, w = draft.value.working_data
  linkForm.value = { client_mode: 'existing', client_id: r.client_id || '', client_name: w.company_name || w.contact_name || '', contact_mode: r.contact_id ? 'existing' : 'none', contact_id: r.contact_id || '', contact_name: w.contact_name, phone: w.phone, email: w.email, site_mode: r.site_id ? 'existing' : 'none', site_id: r.site_id || '', site_title: '', site_address: w.object_address }
  clientQuery.value = r.links.client?.name || w.company_name || w.contact_name || ''
  await searchClients()
  if (r.client_id) { if (!clients.value.some(c => c.id === r.client_id)) clients.value.push({ id: r.client_id, name: r.links.client?.name || `Клиент №${r.client_id}` }); await selectClient(); linkForm.value.contact_id = r.contact_id || ''; linkForm.value.site_id = r.site_id || '' }
}
function saveLink() {
  const f = linkForm.value
  const fields = { client_id: f.client_mode === 'existing' ? Number(f.client_id) : null, new_client: f.client_mode === 'new' ? { name: f.client_name.trim() } : null, contact_id: f.contact_mode === 'existing' ? Number(f.contact_id) : null, new_contact: f.contact_mode === 'new' ? { contact_name: f.contact_name.trim(), phone: nullable(f.phone), email: nullable(f.email) } : null, site_id: f.site_mode === 'existing' ? Number(f.site_id) : null, new_site: f.site_mode === 'new' ? { title: f.site_title.trim(), address: f.site_address.trim() } : null }
  const signature = JSON.stringify(fields)
  if (!pendingLink || pendingLink.signature !== signature) pendingLink = { signature, body: { ...fields, version: request.value.version, command_id: crypto.randomUUID() } }
  action(async () => { const id = request.value.id; try { await api.link(id, pendingLink.body) } catch (e) { if (e.response?.status === 409) pendingLink = null; throw e }; const { data } = await api.getById(id); pendingLink = null; linkOpen.value = false; setRequest(data) }, 'Связи сохранены.')
}
function eventDescription(e) {
  if (e.kind === 'received') return 'Обращение сохранено. Ожидает обработки офисом.'
  if (e.kind === 'linked') return `Клиент №${e.data.after.client_id}${e.data.after.site_id ? ` · Объект №${e.data.after.site_id}` : ''}`
  const after = e.data.after || {}, changes = []
  if ('status' in after) changes.push(`Статус: ${statuses[after.status]}`)
  if ('assigned_user_id' in after) changes.push(`Ответственный: ${assignees.value.find(u => u.id === after.assigned_user_id)?.full_name || (after.assigned_user_id ? `№${after.assigned_user_id}` : 'не назначен')}`)
  if ('working_data' in after) changes.push('Уточнены контактные данные или задача')
  if ('outcome' in after) changes.push(`Итог: ${after.outcome || 'очищен'}`)
  return changes.join(' · ')
}
watch(() => route.params.id, () => { request.value = null; pendingLink = null; notice.value = ''; commentText.value = ''; load() })
onMounted(load)
</script>
