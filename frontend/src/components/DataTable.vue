<template>
  <div>
    <!-- Column settings toolbar -->
    <div class="flex justify-end mb-2 relative dt-root">
      <button
        @click.stop="settingsOpen = !settingsOpen"
        class="btn btn-secondary text-sm flex items-center gap-1"
      >
        <SlidersHorizontal class="w-4 h-4" />Столбцы
      </button>
      <div
        v-if="settingsOpen"
        class="absolute top-10 right-0 z-20 bg-white border border-gray-200 rounded-lg shadow-lg p-3 min-w-[200px]"
        @click.stop
      >
        <div class="flex items-center justify-between mb-2 pb-2 border-b border-gray-100">
          <span class="text-sm font-medium text-gray-700">Отображение столбцов</span>
          <button @click="resetColumns" class="text-xs text-primary-600 hover:underline">По умолчанию</button>
        </div>
        <label
          v-for="col in columnState"
          :key="col.key"
          class="flex items-center gap-2 py-1.5 cursor-pointer text-sm text-gray-700 hover:text-gray-900"
        >
          <input type="checkbox" v-model="col.visible" class="rounded" />
          {{ col.label }}
        </label>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto border border-gray-200 rounded-lg">
      <table class="w-full text-sm text-left" style="table-layout: fixed; border-collapse: collapse">
        <colgroup>
          <col
            v-for="col in visibleColumns"
            :key="col.key"
            :style="{ width: col.width + 'px', minWidth: col.width + 'px' }"
          />
        </colgroup>
        <thead class="bg-gray-50">
          <tr>
            <th
              v-for="col in visibleColumns"
              :key="col.key"
              class="relative px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200 select-none"
              :class="{
                'cursor-pointer hover:bg-gray-100': col.sortable !== false,
                'border-r border-gray-200': col !== visibleColumns[visibleColumns.length - 1],
                'bg-blue-50': dragOverKey === col.key && draggingKey !== col.key,
              }"
              draggable="true"
              @dragstart="onDragStart(col)"
              @dragover.prevent="onDragOver(col)"
              @dragleave="dragOverKey = null"
              @drop.prevent="onDrop(col)"
              @dragend="draggingKey = null; dragOverKey = null"
              @click="onHeaderClick(col)"
            >
              <div class="flex items-center gap-1 overflow-hidden pr-2">
                <GripVertical class="w-3 h-3 text-gray-300 flex-shrink-0 cursor-grab" />
                <span class="truncate">{{ col.label }}</span>
                <span v-if="sort.key === col.key" class="flex-shrink-0">
                  <ChevronUp v-if="sort.dir === 'asc'" class="w-3 h-3 text-primary-600" />
                  <ChevronDown v-else class="w-3 h-3 text-primary-600" />
                </span>
              </div>
              <!-- Resize handle -->
              <div
                class="absolute top-0 right-0 h-full w-2 cursor-col-resize hover:bg-primary-300 opacity-0 hover:opacity-100 transition-opacity"
                @mousedown.prevent.stop="startResize($event, col)"
              />
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-100">
          <tr
            v-for="row in sortedRows"
            :key="row.id"
            class="hover:bg-gray-50 transition-colors"
            :class="rowClass ? rowClass(row) : ''"
            @click="$emit('row-click', row)"
          >
            <td
              v-for="col in visibleColumns"
              :key="col.key"
              class="px-4 py-3 text-gray-900 overflow-hidden"
              :class="{ 'border-r border-gray-100': col !== visibleColumns[visibleColumns.length - 1] }"
              :style="{ maxWidth: col.width + 'px' }"
            >
              <slot :name="col.key" :row="row">
                <span class="truncate block">{{ row[col.key] ?? '—' }}</span>
              </slot>
            </td>
          </tr>
          <tr v-if="sortedRows.length === 0">
            <td :colspan="visibleColumns.length" class="px-4 py-12 text-center text-gray-400">
              <slot name="empty">Нет данных</slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { SlidersHorizontal, ChevronUp, ChevronDown, GripVertical } from 'lucide-vue-next'

const props = defineProps({
  // columns: [{ key, label, width?, defaultVisible?, sortable? }]
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  storageKey: { type: String, default: null },
  rowClass: { type: Function, default: null },
})

defineEmits(['row-click'])

const columnState = ref([])

function buildColumnState(savedMap = {}) {
  return props.columns.map((col, i) => {
    const s = savedMap[col.key]
    return {
      key: col.key,
      label: col.label,
      visible: s ? s.visible : col.defaultVisible !== false,
      width: s?.width ?? col.width ?? 150,
      order: s?.order ?? i,
      sortable: col.sortable !== false,
      defaultVisible: col.defaultVisible !== false,
    }
  }).sort((a, b) => a.order - b.order)
}

function loadState() {
  let savedMap = {}
  if (props.storageKey) {
    try {
      const raw = localStorage.getItem(props.storageKey)
      if (raw) {
        const arr = JSON.parse(raw)
        arr.forEach((x) => { savedMap[x.key] = x })
      }
    } catch {}
  }
  columnState.value = buildColumnState(savedMap)
}

function saveState() {
  if (!props.storageKey) return
  const toSave = columnState.value.map(({ key, visible, width, order }) => ({ key, visible, width, order }))
  localStorage.setItem(props.storageKey, JSON.stringify(toSave))
}

function resetColumns() {
  if (props.storageKey) localStorage.removeItem(props.storageKey)
  columnState.value = buildColumnState()
}

const visibleColumns = computed(() =>
  columnState.value.filter((c) => c.visible).sort((a, b) => a.order - b.order)
)

// ─── Sort ──────────────────────────────────────────────────────────────────
const sort = ref({ key: null, dir: 'asc' })

function onHeaderClick(col) {
  if (col.sortable === false) return
  if (sort.value.key === col.key) {
    sort.value.dir = sort.value.dir === 'asc' ? 'desc' : 'asc'
  } else {
    sort.value.key = col.key
    sort.value.dir = 'asc'
  }
}

const sortedRows = computed(() => {
  if (!sort.value.key) return props.rows
  const key = sort.value.key
  const dir = sort.value.dir === 'asc' ? 1 : -1
  return [...props.rows].sort((a, b) => {
    const av = a[key] ?? ''
    const bv = b[key] ?? ''
    if (av < bv) return -dir
    if (av > bv) return dir
    return 0
  })
})

// ─── Drag to reorder ───────────────────────────────────────────────────────
const draggingKey = ref(null)
const dragOverKey = ref(null)

function onDragStart(col) {
  draggingKey.value = col.key
}
function onDragOver(col) {
  if (col.key !== draggingKey.value) dragOverKey.value = col.key
}
function onDrop(targetCol) {
  if (!draggingKey.value || draggingKey.value === targetCol.key) return
  const cols = [...columnState.value].sort((a, b) => a.order - b.order)
  const fromIdx = cols.findIndex((c) => c.key === draggingKey.value)
  const toIdx = cols.findIndex((c) => c.key === targetCol.key)
  const [moved] = cols.splice(fromIdx, 1)
  cols.splice(toIdx, 0, moved)
  cols.forEach((c, i) => { c.order = i })
  columnState.value = cols
  draggingKey.value = null
  dragOverKey.value = null
  saveState()
}

// ─── Column resize ─────────────────────────────────────────────────────────
const resizing = ref(null)

function startResize(event, col) {
  resizing.value = { col, startX: event.clientX, startWidth: col.width }
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', stopResize)
}
function onResizeMove(event) {
  if (!resizing.value) return
  const { col, startX, startWidth } = resizing.value
  const delta = event.clientX - startX
  const c = columnState.value.find((c) => c.key === col.key)
  if (c) c.width = Math.max(60, startWidth + delta)
}
function stopResize() {
  resizing.value = null
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', stopResize)
  saveState()
}

// ─── Settings dropdown close on outside click ──────────────────────────────
const settingsOpen = ref(false)

function onDocClick(e) {
  if (!e.target.closest('.dt-root')) settingsOpen.value = false
}

// ─── Watch visibility changes → save ──────────────────────────────────────
watch(
  () => columnState.value.map((c) => c.visible),
  saveState
)

onMounted(() => {
  loadState()
  document.addEventListener('click', onDocClick)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', stopResize)
})
</script>
