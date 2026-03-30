<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between px-4 py-3 md:px-6 md:py-4 border-b">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 bg-primary-100 rounded-lg flex items-center justify-center">
            <Building2 class="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h2 class="font-semibold text-gray-900 text-base leading-tight">{{ client.name }}</h2>
            <p v-if="client.inn" class="text-xs text-gray-400">ИНН: {{ client.inn }}</p>
          </div>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 p-1">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Body -->
      <div class="px-4 py-3 md:px-6 md:py-4 space-y-3">
        <!-- Статус -->
        <div class="flex items-center gap-2">
          <span
            class="text-xs px-2 py-0.5 rounded-full font-medium"
            :class="client.is_archived ? 'bg-gray-100 text-gray-500' : client.is_active ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'"
          >
            {{ client.is_archived ? 'Архив' : client.is_active ? 'Активен' : 'Неактивен' }}
          </span>
        </div>

        <!-- Контактное лицо -->
        <div v-if="client.contact_person" class="flex items-start gap-3">
          <User class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <p class="text-xs text-gray-400 mb-0.5">Контактное лицо</p>
            <p class="text-sm text-gray-800">{{ client.contact_person }}</p>
          </div>
        </div>

        <!-- Контакты (телефон) -->
        <div v-if="client.contacts" class="flex items-start gap-3">
          <Phone class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <p class="text-xs text-gray-400 mb-0.5">Контакты</p>
            <p class="text-sm text-gray-800">{{ client.contacts }}</p>
          </div>
        </div>

        <!-- КПП -->
        <div v-if="client.kpp" class="flex items-start gap-3">
          <Hash class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <p class="text-xs text-gray-400 mb-0.5">КПП</p>
            <p class="text-sm text-gray-800">{{ client.kpp }}</p>
          </div>
        </div>

        <!-- Заметки -->
        <div v-if="client.notes" class="flex items-start gap-3">
          <FileText class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <p class="text-xs text-gray-400 mb-0.5">Заметки</p>
            <p class="text-sm text-gray-800 whitespace-pre-line">{{ client.notes }}</p>
          </div>
        </div>

        <!-- Счётчики -->
        <div class="grid grid-cols-3 gap-2 pt-1">
          <div class="bg-blue-50 rounded-lg px-3 py-2 text-center">
            <p class="text-lg font-bold text-blue-700">{{ client.sites_count ?? 0 }}</p>
            <p class="text-xs text-blue-500">Объектов</p>
          </div>
          <div class="bg-violet-50 rounded-lg px-3 py-2 text-center">
            <p class="text-lg font-bold text-violet-700">{{ client.contracts_count ?? 0 }}</p>
            <p class="text-xs text-violet-500">Договоров</p>
          </div>
          <div class="bg-green-50 rounded-lg px-3 py-2 text-center">
            <p class="text-lg font-bold text-green-700">{{ client.visits_count ?? 0 }}</p>
            <p class="text-xs text-green-500">Выездов</p>
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
          Открыть клиента
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Building2, X, User, Phone, Hash, FileText, ExternalLink } from 'lucide-vue-next'

defineProps({
  client: { type: Object, required: true },
})
defineEmits(['close', 'open-page'])
</script>
