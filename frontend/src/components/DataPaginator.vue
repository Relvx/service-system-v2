<template>
  <div class="flex flex-wrap items-center justify-between gap-3 px-1 py-2 text-sm text-gray-600 select-none">
    <!-- Левая часть: строк на странице + итого -->
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-1.5">
        <span class="text-gray-500">Строк:</span>
        <select
          :value="pageSize"
          @change="$emit('update:pageSize', Number($event.target.value))"
          class="border border-gray-200 rounded px-1.5 py-0.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-primary-400"
        >
          <option v-for="s in pageSizes" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <span class="text-gray-400">|</span>
      <span>
        <span class="font-medium text-gray-800">{{ rangeFrom }}–{{ rangeTo }}</span>
        <span class="text-gray-400"> из </span>
        <span class="font-medium text-gray-800">{{ total }}</span>
      </span>
    </div>

    <!-- Правая часть: навигация + reload -->
    <div class="flex items-center gap-1">
      <!-- К первой -->
      <button
        @click="$emit('update:page', 1)"
        :disabled="page <= 1"
        class="p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        title="Первая страница"
      >
        <ChevronsLeft class="w-4 h-4" />
      </button>

      <!-- Предыдущая -->
      <button
        @click="$emit('update:page', page - 1)"
        :disabled="page <= 1"
        class="p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        title="Предыдущая"
      >
        <ChevronLeft class="w-4 h-4" />
      </button>

      <!-- Номер страницы -->
      <div class="flex items-center gap-1 px-1">
        <input
          type="number"
          :value="page"
          :min="1"
          :max="totalPages"
          @change="onPageInput"
          class="w-12 text-center border border-gray-200 rounded px-1 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary-400"
        />
        <span class="text-gray-400">/ {{ totalPages }}</span>
      </div>

      <!-- Следующая -->
      <button
        @click="$emit('update:page', page + 1)"
        :disabled="page >= totalPages"
        class="p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        title="Следующая"
      >
        <ChevronRight class="w-4 h-4" />
      </button>

      <!-- К последней -->
      <button
        @click="$emit('update:page', totalPages)"
        :disabled="page >= totalPages"
        class="p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        title="Последняя страница"
      >
        <ChevronsRight class="w-4 h-4" />
      </button>

      <span class="text-gray-200 mx-1">|</span>

      <!-- Перезагрузка -->
      <button
        @click="$emit('reload')"
        :class="['p-1.5 rounded hover:bg-gray-100 transition-colors', loading ? 'animate-spin text-primary-500' : 'text-gray-500 hover:text-gray-700']"
        title="Обновить"
      >
        <RefreshCw class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, RefreshCw } from 'lucide-vue-next'

const props = defineProps({
  page:     { type: Number, required: true },
  pageSize: { type: Number, required: true },
  total:    { type: Number, required: true },
  loading:  { type: Boolean, default: false },
  pageSizes: { type: Array, default: () => [10, 50, 100] },
})

const emit = defineEmits(['update:page', 'update:pageSize', 'reload'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const rangeFrom  = computed(() => props.total === 0 ? 0 : (props.page - 1) * props.pageSize + 1)
const rangeTo    = computed(() => Math.min(props.page * props.pageSize, props.total))

function onPageInput(e) {
  const v = parseInt(e.target.value)
  if (!isNaN(v) && v >= 1 && v <= totalPages.value) {
    emit('update:page', v)
  } else {
    e.target.value = props.page
  }
}
</script>
