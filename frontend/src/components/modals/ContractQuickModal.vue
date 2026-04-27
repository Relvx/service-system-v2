<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div role="dialog" aria-modal="true" aria-labelledby="ctqm-title" class="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between px-4 py-3 md:px-6 md:py-4 border-b">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 bg-blue-100 rounded-lg flex items-center justify-center">
            <FileText class="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h2 id="ctqm-title" class="font-semibold text-gray-900 text-base leading-tight">
              {{ contract.contract_number || 'Без номера' }}
            </h2>
            <p v-if="contract.subject" class="text-xs text-gray-600 truncate max-w-[240px]">{{ contract.subject }}</p>
          </div>
        </div>
        <button @click="$emit('close')" aria-label="Закрыть" class="text-gray-400 hover:text-gray-600 p-1">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Body -->
      <div class="px-4 py-3 md:px-6 md:py-4 space-y-3">
        <!-- Статус -->
        <div class="flex items-center gap-2">
          <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="statusClass(contract.status)">
            {{ statusLabel(contract.status) }}
          </span>
        </div>

        <!-- Клиент -->
        <div v-if="contract.client_name" class="flex items-start gap-3">
          <Building2 class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <p class="text-xs text-gray-400 mb-0.5">Клиент</p>
            <button
              class="text-sm text-primary-600 hover:underline text-left"
              @click="$emit('open-client')"
            >{{ contract.client_name }}</button>
          </div>
        </div>

        <!-- Дата -->
        <div v-if="contract.contract_date" class="flex items-start gap-3">
          <Calendar class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <p class="text-xs text-gray-400 mb-0.5">Дата договора</p>
            <p class="text-sm text-gray-800">{{ formatDate(contract.contract_date) }}</p>
          </div>
        </div>

        <!-- Суммы -->
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-blue-50 rounded-lg px-3 py-2">
            <p class="text-xs text-blue-400 mb-0.5">Сумма договора</p>
            <p v-if="contract.amount" class="text-sm font-semibold text-blue-800">{{ formatAmount(contract.amount) }} ₽</p>
            <p v-else class="text-sm text-gray-400">—</p>
          </div>
          <div class="bg-indigo-50 rounded-lg px-3 py-2">
            <p class="text-xs text-indigo-400 mb-0.5">Сумма акта</p>
            <p v-if="contract.act_amount" class="text-sm font-semibold text-indigo-800">{{ formatAmount(contract.act_amount) }} ₽</p>
            <p v-else class="text-sm text-gray-400">—</p>
          </div>
        </div>

        <!-- Объекты -->
        <div v-if="contract.sites && contract.sites.length">
          <p class="text-xs text-gray-400 mb-1.5">Объекты ({{ contract.sites.length }})</p>
          <div class="space-y-1 max-h-36 overflow-y-auto">
            <div
              v-for="s in contract.sites"
              :key="s.id"
              class="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-gray-50 hover:bg-green-50 cursor-pointer group"
              @click="$emit('open-site', s)"
            >
              <MapPin class="w-3.5 h-3.5 text-gray-400 group-hover:text-green-600 flex-shrink-0" />
              <div class="min-w-0">
                <p class="text-sm text-gray-700 group-hover:text-green-700 truncate">{{ s.title }}</p>
                <p class="text-xs text-gray-400 truncate">{{ s.address }}</p>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="(contract.sites_count || 0) === 0" class="text-sm text-gray-400 italic">
          Объекты не привязаны
        </div>

        <!-- Заметки -->
        <div v-if="contract.notes" class="flex items-start gap-3">
          <StickyNote class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <p class="text-xs text-gray-400 mb-0.5">Заметки</p>
            <p class="text-sm text-gray-800 whitespace-pre-line">{{ contract.notes }}</p>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-4 py-3 md:px-6 md:py-4 border-t flex justify-end">
        <button
          @click="$emit('open-page')"
          class="btn btn-primary flex items-center gap-2"
        >
          <ExternalLink class="w-4 h-4" />
          Открыть договор
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { FileText, X, Building2, Calendar, MapPin, ExternalLink, StickyNote } from 'lucide-vue-next'

defineProps({
  contract: { type: Object, required: true },
})
defineEmits(['close', 'open-page', 'open-client', 'open-site'])

function statusClass(s) {
  const m = { active: 'bg-green-100 text-green-700', closed: 'bg-gray-200 text-gray-600', cancelled: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-600'
}
function statusLabel(s) {
  const m = { active: 'Активен', closed: 'Закрыт', cancelled: 'Отменён' }
  return m[s] || s
}
function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }
function formatAmount(v) { return Number(v).toLocaleString('ru-RU') }
</script>
