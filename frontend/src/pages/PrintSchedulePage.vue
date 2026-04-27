<template>
  <div class="print-page">
    <!-- Шапка -->
    <div class="print-header">
      <h1>Расписание на {{ monthName }} {{ year }}</h1>
      <p class="print-meta">Сформировано: {{ today }}</p>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="print-loading no-print">
      <p>Загрузка данных...</p>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="no-print">
      <p>Ошибка загрузки: {{ error }}</p>
    </div>

    <!-- Таблица -->
    <table v-else class="print-table">
      <thead>
        <tr>
          <th class="col-num">#</th>
          <th class="col-client">Клиент</th>
          <th class="col-contract">Договор</th>
          <th class="col-addresses">Адреса объектов</th>
          <th class="col-contact">Контакт</th>
          <th class="col-note">Пометки</th>
          <th class="col-visits">Последние выезды</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, idx) in rows" :key="row.contract_id">
          <td class="col-num">{{ idx + 1 }}</td>
          <td class="col-client">{{ row.client_name }}</td>
          <td class="col-contract">{{ row.contract_number }}</td>
          <td class="col-addresses">
            <div v-if="row.site_addresses && row.site_addresses.length" class="addresses-list">
              <div v-for="addr in row.site_addresses" :key="addr" class="address-item">{{ addr }}</div>
            </div>
            <span v-else class="no-visits">—</span>
          </td>
          <td class="col-contact">
            <div v-if="row.contact_name || row.contact_phone">
              <div v-if="row.contact_name">{{ row.contact_name }}</div>
              <div v-if="row.contact_phone" class="contact-phone">{{ row.contact_phone }}</div>
            </div>
            <span v-else class="no-visits">—</span>
          </td>
          <td class="col-note">{{ row.note || '' }}</td>
          <td class="col-visits">
            <div v-if="row.visits && row.visits.length" class="visits-list">
              <div v-for="v in row.visits" :key="v.id" class="visit-item">
                <span class="visit-date">{{ formatDate(v.planned_date) }}</span>
                <span v-if="v.work_summary" class="visit-summary"> — {{ v.work_summary }}</span>
              </div>
            </div>
            <span v-else class="no-visits">—</span>
          </td>
        </tr>
        <tr v-if="rows.length === 0">
          <td colspan="7" class="empty-row">Нет договоров в этом месяце</td>
        </tr>
      </tbody>
    </table>

    <!-- Подвал -->
    <div v-if="!loading && !error" class="print-footer">
      Всего: {{ rows.length }} {{ pluralContracts(rows.length) }}
    </div>

    <!-- Кнопка закрыть (скрывается при печати) -->
    <div class="no-print close-btn-wrap">
      <button @click="closeWindow">Закрыть</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { scheduleAPI, visitsAPI } from '../services/api.js'

const route = useRoute()
const year = Number(route.params.year)
const month = Number(route.params.month)

const MONTHS_FULL = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

const monthName = computed(() => MONTHS_FULL[month - 1])

const now = new Date()
const today = `${String(now.getDate()).padStart(2, '0')}.${String(now.getMonth() + 1).padStart(2, '0')}.${now.getFullYear()}`

const loading = ref(true)
const error = ref(null)
const rows = ref([])

function closeWindow() {
  window.close()
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-')
  return `${d}.${m}.${y}`
}

function pluralContracts(n) {
  if (n % 10 === 1 && n % 100 !== 11) return 'договор'
  if ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100)) return 'договора'
  return 'договоров'
}

onMounted(async () => {
  try {
    const schedRes = await scheduleAPI.getMonth(year, month)
    const items = schedRes.data.items

    // Параллельно запрашиваем последние 5 выездов для каждого договора
    const visitsResults = await Promise.all(
      items.map(item =>
        visitsAPI.getAll({ contract_id: item.contract_id, status: 'done', limit: 5 })
          .then(r => r.data.items)
          .catch(() => [])
      )
    )

    rows.value = items.map((item, i) => ({
      ...item,
      visits: visitsResults[i] || [],
    }))
  } catch (e) {
    error.value = e?.message || 'Неизвестная ошибка'
  } finally {
    loading.value = false
    if (!error.value) {
      // Небольшая задержка чтобы Vue успел отрендерить таблицу
      setTimeout(() => window.print(), 300)
    }
  }
})
</script>

<style>
* { box-sizing: border-box; }

body { margin: 0; font-family: Arial, sans-serif; font-size: 11pt; color: #000; }

.print-page { padding: 10mm; }

.print-header { margin-bottom: 6mm; }
.print-header h1 { font-size: 16pt; margin: 0 0 2mm 0; }
.print-meta { font-size: 9pt; color: #666; margin: 0; }

.print-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 4mm;
}
.print-table th,
.print-table td {
  border: 1px solid #999;
  padding: 2mm 3mm;
  vertical-align: top;
  text-align: left;
}
.print-table th { background: #f0f0f0; font-weight: bold; font-size: 10pt; }

.col-num       { width: 6mm; text-align: center; }
.col-client    { width: 16%; }
.col-contract  { width: 13%; }
.col-addresses { width: 20%; }
.col-contact   { width: 13%; }
.col-note      { width: 11%; }
.col-visits    { width: auto; }

.addresses-list { display: flex; flex-direction: column; gap: 0.5mm; }
.address-item { font-size: 9pt; }

.contact-phone { font-size: 9pt; color: #555; }

.visits-list { display: flex; flex-direction: column; gap: 1mm; }
.visit-date { font-weight: 600; }
.visit-summary { color: #333; }
.no-visits { color: #999; }
.empty-row { text-align: center; color: #999; padding: 4mm; }

.print-footer { font-size: 9pt; color: #555; margin-top: 3mm; }

.print-loading { text-align: center; padding: 20mm; color: #666; }

.close-btn-wrap { margin-top: 6mm; text-align: right; }
.close-btn-wrap button {
  padding: 6px 16px; cursor: pointer;
  border: 1px solid #ccc; border-radius: 4px;
  background: #f5f5f5; font-size: 11pt;
}

@page { size: A4 landscape; margin: 10mm; }
@media print { .no-print { display: none !important; } }
</style>
