<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div role="dialog" aria-modal="true" aria-labelledby="ctlm-title" class="bg-white rounded-xl shadow-2xl w-full max-w-sm mx-4">
      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b">
        <div class="flex items-center gap-2">
          <FileText class="w-5 h-5 text-blue-600" />
          <h2 id="ctlm-title" class="font-semibold text-gray-900">Договоры ({{ contracts.length }})</h2>
        </div>
        <button @click="$emit('close')" aria-label="Закрыть" class="text-gray-400 hover:text-gray-600 p-1">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- List -->
      <div class="py-2 max-h-80 overflow-y-auto">
        <button
          v-for="contract in contracts"
          :key="contract.id"
          class="w-full flex items-center gap-3 px-5 py-3 hover:bg-blue-50 group text-left transition-colors"
          @click="$emit('select', contract)"
        >
          <div class="w-8 h-8 bg-blue-100 rounded-lg flex-shrink-0 flex items-center justify-center group-hover:bg-blue-200">
            <FileText class="w-4 h-4 text-blue-600" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium text-gray-800 group-hover:text-blue-700 truncate">
              {{ contract.contract_number || 'Без номера' }}
            </p>
            <div class="flex items-center gap-2 mt-0.5">
              <span v-if="contract.contract_date" class="text-xs text-gray-400">{{ formatDate(contract.contract_date) }}</span>
              <span class="text-xs px-1.5 py-0.5 rounded-full font-medium" :class="statusClass(contract.status)">
                {{ statusLabel(contract.status) }}
              </span>
            </div>
          </div>
          <ChevronRight class="w-4 h-4 text-gray-300 group-hover:text-blue-500 flex-shrink-0" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { FileText, X, ChevronRight } from 'lucide-vue-next'

defineProps({
  contracts: { type: Array, required: true },
})
defineEmits(['close', 'select'])

function statusClass(s) {
  const m = { active: 'bg-green-100 text-green-700', closed: 'bg-gray-200 text-gray-600', cancelled: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-600'
}
function statusLabel(s) {
  const m = { active: 'Активен', closed: 'Закрыт', cancelled: 'Отменён' }
  return m[s] || s
}
function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }
</script>
