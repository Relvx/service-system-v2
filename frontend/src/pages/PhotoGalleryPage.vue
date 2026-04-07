<template>
  <Layout>
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold text-gray-900">Галерея фотографий</h1>
        <span class="text-sm text-gray-500">{{ total }} фото</span>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-3 mb-6">
        <input
          v-model="filterClient"
          @input="onFilterChange"
          placeholder="Клиент..."
          class="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 w-48"
        />
        <button
          v-if="filterClient"
          @click="filterClient = ''; onFilterChange()"
          class="px-3 py-2 text-sm text-gray-500 hover:text-gray-700 border border-gray-200 rounded-lg"
        >
          Сбросить
        </button>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading && items.length === 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        <div
          v-for="i in 20"
          :key="i"
          class="aspect-square bg-gray-200 rounded-lg animate-pulse"
        />
      </div>

      <!-- Empty state -->
      <div v-else-if="!loading && items.length === 0" class="text-center py-20 text-gray-400">
        <Images class="w-12 h-12 mx-auto mb-3 opacity-40" />
        <p class="text-sm">Фотографий пока нет</p>
      </div>

      <!-- Grid -->
      <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        <div
          v-for="item in items"
          :key="item.id"
          @click="openModal(item)"
          class="group relative aspect-square bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-primary-400 transition-all"
        >
          <img
            :src="item.file_url"
            :alt="item.file_name || 'Фото'"
            class="w-full h-full object-cover"
            loading="lazy"
          />
          <!-- Overlay on hover -->
          <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-end">
            <div class="p-2 text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity w-full">
              <p v-if="item.site_title" class="truncate font-medium">{{ item.site_title }}</p>
              <p v-if="item.visit_date" class="opacity-80">{{ formatDate(item.visit_date) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Load more -->
      <div v-if="items.length < total" class="mt-6 flex justify-center">
        <button
          @click="loadMore"
          :disabled="loading"
          class="px-6 py-2 bg-white border border-gray-200 text-sm text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
        >
          {{ loading ? 'Загрузка...' : `Показать ещё (${total - items.length})` }}
        </button>
      </div>
    </div>

    <!-- Modal -->
    <div
      v-if="selected"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80"
      @click.self="closeModal"
      @keydown.escape="closeModal"
    >
      <div class="relative max-w-4xl w-full mx-4 flex flex-col md:flex-row bg-white rounded-xl overflow-hidden shadow-2xl max-h-[90vh]">
        <!-- Close button -->
        <button
          @click="closeModal"
          class="absolute top-3 right-3 z-10 w-8 h-8 flex items-center justify-center rounded-full bg-black bg-opacity-40 text-white hover:bg-opacity-60 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>

        <!-- Photo -->
        <div class="flex-1 bg-black flex items-center justify-center min-h-48">
          <img
            :src="selected.file_url"
            :alt="selected.file_name || 'Фото'"
            class="max-h-[60vh] md:max-h-[80vh] max-w-full object-contain"
          />
        </div>

        <!-- Info panel -->
        <div class="w-full md:w-72 flex-shrink-0 p-5 flex flex-col gap-4 overflow-y-auto">
          <h2 class="text-base font-semibold text-gray-900">Информация</h2>

          <div v-if="selected.visit_date" class="flex items-start gap-3">
            <Calendar class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div>
              <p class="text-xs text-gray-500">Дата выезда</p>
              <p class="text-sm font-medium text-gray-900">{{ formatDate(selected.visit_date) }}</p>
            </div>
          </div>

          <div v-if="selected.site_title" class="flex items-start gap-3">
            <Building2 class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div>
              <p class="text-xs text-gray-500">Объект</p>
              <RouterLink
                v-if="selected.site_id"
                :to="`/sites/${selected.site_id}`"
                class="text-sm font-medium text-primary-600 hover:underline"
                @click="closeModal"
              >{{ selected.site_title }}</RouterLink>
              <p v-else class="text-sm font-medium text-gray-900">{{ selected.site_title }}</p>
            </div>
          </div>

          <div v-if="selected.client_name" class="flex items-start gap-3">
            <Users class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div>
              <p class="text-xs text-gray-500">Клиент</p>
              <RouterLink
                v-if="selected.client_id"
                :to="`/clients/${selected.client_id}`"
                class="text-sm font-medium text-primary-600 hover:underline"
                @click="closeModal"
              >{{ selected.client_name }}</RouterLink>
              <p v-else class="text-sm font-medium text-gray-900">{{ selected.client_name }}</p>
            </div>
          </div>

          <div class="flex items-start gap-3">
            <Clock class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div>
              <p class="text-xs text-gray-500">Загружено</p>
              <p class="text-sm text-gray-700">{{ formatDateTime(selected.created_at) }}</p>
            </div>
          </div>

          <div class="mt-auto pt-4 border-t border-gray-100 flex flex-col gap-2">
            <RouterLink
              v-if="selected.visit_id"
              :to="`/visits?visit_id=${selected.visit_id}`"
              class="w-full text-center px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
              @click="closeModal"
            >
              Перейти к выезду
            </RouterLink>
            <a
              :href="selected.file_url"
              target="_blank"
              rel="noopener"
              class="w-full text-center px-4 py-2 border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
            >
              Открыть оригинал
            </a>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import { Images, X, Calendar, Building2, Users, Clock } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { attachmentsAPI } from '../services/api.js'

const LIMIT = 20

const items = ref([])
const total = ref(0)
const loading = ref(false)
const selected = ref(null)
const filterClient = ref('')

let filterTimeout = null

async function load(reset = false) {
  if (loading.value) return
  loading.value = true
  try {
    const params = { limit: LIMIT, offset: reset ? 0 : items.value.length }
    if (filterClient.value.trim()) params.client_name = filterClient.value.trim()
    const res = await attachmentsAPI.getGallery(params)
    if (reset) {
      items.value = res.data.items
    } else {
      items.value.push(...res.data.items)
    }
    total.value = res.data.total
  } catch {
    /* ignore */
  } finally {
    loading.value = false
  }
}

function loadMore() {
  load(false)
}

function onFilterChange() {
  clearTimeout(filterTimeout)
  filterTimeout = setTimeout(() => load(true), 350)
}

function openModal(item) {
  selected.value = item
  document.body.style.overflow = 'hidden'
}

function closeModal() {
  selected.value = null
  document.body.style.overflow = ''
}

function onKeydown(e) {
  if (e.key === 'Escape') closeModal()
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatDateTime(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  load(true)
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>
