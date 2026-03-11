<template>
  <Layout>
    <div class="flex h-[calc(100vh-8rem)] gap-4">
      <!-- Sidebar -->
      <div class="w-80 flex flex-col gap-4 overflow-hidden">
        <div class="card">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input v-model="search" type="text" placeholder="Поиск объекта..." class="input pl-10" />
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
              <!-- Active visit badge -->
              <div v-if="activeVisitBySite[s.id]" class="mt-1.5 flex items-center gap-1 text-xs text-green-700 bg-green-50 rounded px-2 py-0.5">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-green-500"></span>
                {{ cfg.visitStatusLabel(activeVisitBySite[s.id].status) }} · {{ activeVisitBySite[s.id].master_name || 'Без мастера' }}
              </div>
            </div>
            <div v-if="filteredSites.length === 0" class="text-center py-4 text-gray-500 text-sm">
              Объекты не найдены
            </div>
          </div>
        </div>
      </div>

      <!-- Map -->
      <div class="flex-1 card p-0 overflow-hidden relative">
        <div ref="mapContainer" class="w-full h-full rounded-lg"></div>
        <div v-if="!loading && sites.length === 0" class="absolute inset-0 flex items-center justify-center text-gray-500">
          Нет объектов с координатами
        </div>

        <!-- Legend -->
        <div class="absolute bottom-4 left-4 bg-white rounded-lg shadow border border-gray-200 px-3 py-2 flex items-center gap-4 text-xs text-gray-600 z-10">
          <div class="flex items-center gap-1.5">
            <span class="inline-block w-3 h-3 rounded-full bg-green-500"></span>Активный выезд
          </div>
          <div class="flex items-center gap-1.5">
            <span class="inline-block w-3 h-3 rounded-full bg-gray-500"></span>Нет выездов
          </div>
        </div>

        <!-- Site popup -->
        <div
          v-if="popupSite"
          class="absolute top-4 right-4 w-72 bg-white rounded-lg shadow-xl border border-gray-200 z-10"
        >
          <div class="flex items-center justify-between p-4 border-b">
            <h3 class="font-semibold text-gray-900 text-sm">{{ popupSite.title }}</h3>
            <button @click="popupSite = null" class="text-gray-400 hover:text-gray-600">
              <X class="w-4 h-4" />
            </button>
          </div>
          <div class="p-4 space-y-2 text-sm">
            <div v-if="popupSite.address" class="text-gray-600">{{ popupSite.address }}</div>
            <div v-if="popupSite.client_name" class="text-gray-500 text-xs">{{ popupSite.client_name }}</div>
            <template v-if="popupActiveVisit">
              <div class="border-t pt-2 mt-2">
                <p class="text-xs font-medium text-gray-500 mb-1">Активный выезд</p>
                <div class="flex items-center gap-2 mb-1">
                  <span
                    class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full"
                    :class="visitStatusClass(popupActiveVisit.status)"
                  >
                    {{ cfg.visitStatusLabel(popupActiveVisit.status) }}
                  </span>
                  <span class="text-xs text-gray-500">{{ formatDate(popupActiveVisit.planned_date) }}</span>
                </div>
                <p class="text-xs text-gray-600">Мастер: {{ popupActiveVisit.master_name || 'Не назначен' }}</p>
              </div>
            </template>
            <div v-else class="text-xs text-gray-400 italic border-t pt-2 mt-2">Нет активных выездов</div>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { Search, Building2, X } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { useAuthStore } from '../stores/auth.js'
import { useConfigStore } from '../stores/config.js'
import { sitesAPI, visitsAPI } from '../services/api.js'

const auth = useAuthStore()
const cfg = useConfigStore()
const mapContainer = ref(null)
const sites = ref([])
const loading = ref(true)
const search = ref('')
const selectedSiteId = ref(null)
const popupSite = ref(null)
const activeVisits = ref([])

let mapInstance = null
let mapglLib = null
const markers = {}

const filteredSites = computed(() => {
  if (!search.value) return sites.value
  const q = search.value.toLowerCase()
  return sites.value.filter(
    (s) => s.title.toLowerCase().includes(q) || s.address?.toLowerCase().includes(q)
  )
})

// Map: site_id → active visit (planned or in_progress today or future)
const activeVisitBySite = computed(() => {
  const map = {}
  for (const v of activeVisits.value) {
    if (!map[v.site_id]) map[v.site_id] = v
  }
  return map
})

const popupActiveVisit = computed(() =>
  popupSite.value ? activeVisitBySite.value[popupSite.value.id] || null : null
)

function selectSite(s) {
  selectedSiteId.value = s.id
  popupSite.value = s
  if (mapInstance && s.longitude && s.latitude) {
    mapInstance.setCenter([s.longitude, s.latitude], { animate: true })
    mapInstance.setZoom(15, { animate: true })
  }
}

function visitStatusClass(s) {
  const m = {
    planned: 'bg-blue-100 text-blue-700',
    in_progress: 'bg-green-100 text-green-700',
    done: 'bg-gray-100 text-gray-600',
    closed: 'bg-gray-100 text-gray-600',
    cancelled: 'bg-red-100 text-red-600',
  }
  return m[s] || 'bg-gray-100 text-gray-600'
}

function formatDate(d) {
  return d ? new Date(d.slice(0, 10) + 'T00:00:00').toLocaleDateString('ru-RU') : ''
}

function markerIcon(color) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="42" viewBox="0 0 32 42">
    <path d="M16 0C7.163 0 0 7.163 0 16c0 5.514 2.789 10.388 7.04 13.343L16 42l8.96-12.657C29.211 26.388 32 21.514 32 16 32 7.163 24.837 0 16 0z" fill="${color}"/>
    <circle cx="16" cy="16" r="7" fill="white"/>
  </svg>`
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg)
}

const ICON_DEFAULT = markerIcon('#6b7280')
const ICON_ACTIVE  = markerIcon('#22c55e')

async function initMap() {
  const { load } = await import('@2gis/mapgl')
  mapglLib = await load()

  const apiKey = import.meta.env.VITE_2GIS_KEY
  mapInstance = new mapglLib.Map(mapContainer.value, {
    center: [37.62, 55.75],
    zoom: 10,
    key: apiKey,
  })

  sites.value.forEach((s) => {
    if (!s.latitude || !s.longitude) return
    const hasActive = !!activeVisitBySite.value[s.id]
    const marker = new mapglLib.Marker(mapInstance, {
      coordinates: [s.longitude, s.latitude],
      icon: {
        url: hasActive ? ICON_ACTIVE : ICON_DEFAULT,
        size: [32, 42],
        anchor: [16, 42],
      },
    })
    marker.on('click', () => selectSite(s))
    markers[s.id] = marker
  })
}

onMounted(async () => {
  try {
    const today = new Date().toISOString().slice(0, 10)
    const isMaster =
      auth.hasGroup('master_group') &&
      !auth.hasGroup('office_group') &&
      !auth.hasGroup('admin_group')

    const [sitesRes, visitsRes] = await Promise.all([
      sitesAPI.getAll({ active_only: true }),
      isMaster
        ? visitsAPI.getAll({ master_id: auth.user?.id, date_from: today })
        : visitsAPI.getAll({ date_from: today }),
    ])

    sites.value = sitesRes.data.filter((s) => s.latitude && s.longitude)
    activeVisits.value = visitsRes.data.filter(
      (v) => v.status !== 'cancelled' && v.status !== 'closed'
    )
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
