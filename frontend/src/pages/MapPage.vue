<template>
  <Layout>
    <div class="flex h-[calc(100vh-8rem)] gap-4">
      <!-- Sidebar -->
      <div class="w-80 flex flex-col gap-4 overflow-hidden">
        <div class="card">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input v-model="search" type="text" placeholder="Поиск объекта..." class="input pl-10" @input="filterSites" />
          </div>
        </div>

        <div class="card flex-1 overflow-y-auto">
          <div v-if="loading" class="flex justify-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="s in filteredSites"
              :key="s.id"
              @click="selectSite(s)"
              class="p-3 rounded-lg cursor-pointer transition-colors"
              :class="selectedSiteId === s.id ? 'bg-primary-50 border border-primary-200' : 'hover:bg-gray-50'"
            >
              <div class="flex items-center gap-2">
                <Building2 class="w-4 h-4 text-gray-500 flex-shrink-0" />
                <div class="min-w-0">
                  <p class="font-medium text-sm text-gray-900 truncate">{{ s.title }}</p>
                  <p class="text-xs text-gray-500 truncate">{{ s.address }}</p>
                  <p v-if="s.client_name" class="text-xs text-gray-400 truncate">{{ s.client_name }}</p>
                </div>
              </div>
            </div>
            <div v-if="filteredSites.length === 0" class="text-center py-4 text-gray-500 text-sm">
              Объекты не найдены
            </div>
          </div>
        </div>
      </div>

      <!-- Map -->
      <div class="flex-1 card p-0 overflow-hidden">
        <div ref="mapContainer" class="w-full h-full rounded-lg"></div>
        <div v-if="!loading && sites.length === 0" class="absolute inset-0 flex items-center justify-center text-gray-500">
          Нет объектов с координатами
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { Search, Building2 } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { sitesAPI } from '../services/api.js'

const mapContainer = ref(null)
const sites = ref([])
const loading = ref(true)
const search = ref('')
const selectedSiteId = ref(null)

let mapInstance = null
let mapglLib = null
const markers = {}

const filteredSites = computed(() => {
  if (!search.value) return sites.value
  const q = search.value.toLowerCase()
  return sites.value.filter((s) => s.title.toLowerCase().includes(q) || s.address.toLowerCase().includes(q))
})

function filterSites() {
  // reactive computed handles filtering
}

function selectSite(s) {
  selectedSiteId.value = s.id
  if (mapInstance && s.longitude && s.latitude) {
    mapInstance.setCenter([s.longitude, s.latitude], { animate: true })
    mapInstance.setZoom(15, { animate: true })
  }
}

async function initMap() {
  const { load } = await import('@2gis/mapgl')
  mapglLib = await load()

  const apiKey = import.meta.env.VITE_2GIS_KEY
  mapInstance = new mapglLib.Map(mapContainer.value, {
    center: [37.62, 55.75],
    zoom: 10,
    key: apiKey,
  })

  // Add markers for all sites with coordinates
  sites.value.forEach((s) => {
    if (!s.latitude || !s.longitude) return
    const marker = new mapglLib.Marker(mapInstance, {
      coordinates: [s.longitude, s.latitude],
    })
    marker.on('click', () => selectSite(s))
    markers[s.id] = marker
  })
}

onMounted(async () => {
  try {
    const res = await sitesAPI.getAll({ active_only: true })
    sites.value = res.data.filter((s) => s.latitude && s.longitude)
  } finally {
    loading.value = false
  }

  if (mapContainer.value) {
    await initMap()
  }
})

onBeforeUnmount(() => {
  Object.values(markers).forEach((m) => m.destroy())
  if (mapInstance) mapInstance.destroy()
})
</script>
