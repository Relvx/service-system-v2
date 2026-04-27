<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div role="dialog" aria-modal="true" aria-labelledby="slm-title" class="bg-white rounded-xl shadow-2xl w-full max-w-sm mx-4">
      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b">
        <div class="flex items-center gap-2">
          <MapPin class="w-5 h-5 text-green-600" />
          <h2 id="slm-title" class="font-semibold text-gray-900">Объекты ({{ sites.length }})</h2>
        </div>
        <button @click="$emit('close')" aria-label="Закрыть" class="text-gray-400 hover:text-gray-600 p-1">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- List -->
      <div class="py-2 max-h-80 overflow-y-auto">
        <button
          v-for="site in sites"
          :key="site.id"
          class="w-full flex items-center gap-3 px-5 py-3 hover:bg-green-50 group text-left transition-colors"
          @click="$emit('select', site)"
        >
          <div class="w-8 h-8 bg-green-100 rounded-lg flex-shrink-0 flex items-center justify-center group-hover:bg-green-200">
            <Building2 class="w-4 h-4 text-green-600" />
          </div>
          <div class="min-w-0">
            <p class="text-sm font-medium text-gray-800 group-hover:text-green-700 truncate">{{ site.title }}</p>
            <p class="text-xs text-gray-600 truncate">{{ site.address }}</p>
          </div>
          <ChevronRight class="w-4 h-4 text-gray-300 group-hover:text-green-500 flex-shrink-0 ml-auto" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { MapPin, X, Building2, ChevronRight } from 'lucide-vue-next'

defineProps({
  sites: { type: Array, required: true },
})
defineEmits(['close', 'select'])
</script>
