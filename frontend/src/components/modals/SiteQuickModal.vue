<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div role="dialog" aria-modal="true" aria-labelledby="sqm-title" class="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between px-4 py-3 md:px-6 md:py-4 border-b">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 bg-green-100 rounded-lg flex items-center justify-center">
            <Building2 class="w-5 h-5 text-green-600" />
          </div>
          <div>
            <h2 id="sqm-title" class="font-semibold text-gray-900 text-base leading-tight">{{ site.title }}</h2>
            <p v-if="site.address" class="text-xs text-gray-600 truncate max-w-[240px]">{{ site.address }}</p>
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
          <span class="text-xs px-2 py-0.5 rounded-full font-medium"
            :class="site.is_archived ? 'bg-gray-100 text-gray-500' : 'bg-green-100 text-green-700'">
            {{ site.is_archived ? 'Архив' : 'Активен' }}
          </span>
          <span v-if="site.service_frequency" class="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">
            {{ cfg.serviceFrequencyLabel(site.service_frequency) }}
          </span>
        </div>

        <!-- Клиент -->
        <div v-if="site.client_name" class="flex items-start gap-3">
          <Building2 class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <p class="text-xs text-gray-400 mb-0.5">Клиент</p>
            <button
              class="text-sm text-primary-600 hover:underline text-left"
              @click="$emit('open-client')"
            >{{ site.client_name }}</button>
          </div>
        </div>

        <!-- Контакт на месте -->
        <div v-if="site.onsite_contact" class="flex items-start gap-3">
          <Phone class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <p class="text-xs text-gray-400 mb-0.5">Контакт на месте</p>
            <p class="text-sm text-gray-800">{{ site.onsite_contact }}</p>
          </div>
        </div>

        <!-- Доступ -->
        <div v-if="site.access_notes" class="flex items-start gap-3">
          <KeyRound class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <p class="text-xs text-gray-400 mb-0.5">Доступ</p>
            <p class="text-sm text-gray-800 whitespace-pre-line">{{ site.access_notes }}</p>
          </div>
        </div>

        <!-- Координаты -->
        <div v-if="site.latitude && site.longitude" class="flex items-start gap-3">
          <MapPin class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <p class="text-xs text-gray-400 mb-0.5">Координаты</p>
            <p class="text-sm text-gray-600 font-mono">{{ site.latitude }}, {{ site.longitude }}</p>
          </div>
        </div>

        <!-- Стоимость выездов -->
        <div v-if="site.price_maintenance || site.price_repair || site.price_emergency">
          <p class="text-xs text-gray-400 mb-1.5">Стоимость выездов</p>
          <div class="grid grid-cols-3 gap-2">
            <div v-if="site.price_maintenance" class="bg-gray-50 rounded-lg px-2 py-1.5 text-center">
              <p class="text-sm font-semibold text-gray-800">{{ formatAmount(site.price_maintenance) }} ₽</p>
              <p class="text-xs text-gray-400">ТО</p>
            </div>
            <div v-if="site.price_repair" class="bg-gray-50 rounded-lg px-2 py-1.5 text-center">
              <p class="text-sm font-semibold text-gray-800">{{ formatAmount(site.price_repair) }} ₽</p>
              <p class="text-xs text-gray-400">Ремонт</p>
            </div>
            <div v-if="site.price_emergency" class="bg-gray-50 rounded-lg px-2 py-1.5 text-center">
              <p class="text-sm font-semibold text-gray-800">{{ formatAmount(site.price_emergency) }} ₽</p>
              <p class="text-xs text-gray-400">Аварийный</p>
            </div>
          </div>
        </div>

        <!-- Выезды -->
        <div class="bg-green-50 rounded-lg px-3 py-2 flex items-center justify-between">
          <span class="text-sm text-green-700">Всего выездов</span>
          <span class="text-lg font-bold text-green-700">{{ site.total_visits ?? 0 }}</span>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-4 py-3 md:px-6 md:py-4 border-t flex justify-end">
        <button
          @click="$emit('open-page')"
          class="btn btn-primary flex items-center gap-2"
        >
          <ExternalLink class="w-4 h-4" />
          Открыть объект
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Building2, X, Phone, KeyRound, MapPin, ExternalLink } from 'lucide-vue-next'
import { useConfigStore } from '../../stores/config.js'

const cfg = useConfigStore()

defineProps({
  site: { type: Object, required: true },
})
defineEmits(['close', 'open-page', 'open-client'])

function formatAmount(v) { return Number(v).toLocaleString('ru-RU') }
</script>
