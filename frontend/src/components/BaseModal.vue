<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="emit('close')"
    >
      <div
        ref="dialogEl"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        class="bg-white rounded-lg shadow-xl w-full mx-4 max-h-[90vh] flex flex-col"
        :class="maxWidth"
      >
        <div class="flex items-center justify-between p-6 border-b flex-shrink-0">
          <h2 :id="titleId" class="text-xl font-semibold text-gray-900">{{ title }}</h2>
          <button
            type="button"
            @click="emit('close')"
            aria-label="Закрыть"
            class="text-gray-600 hover:text-gray-900 transition-colors"
          >
            <X class="w-6 h-6" />
          </button>
        </div>
        <div class="overflow-y-auto">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { X } from 'lucide-vue-next'

const props = defineProps({
  title: { type: String, required: true },
  maxWidth: { type: String, default: 'max-w-lg' },
})
const emit = defineEmits(['close'])

const dialogEl = ref(null)
const titleId = `modal-title-${Math.random().toString(36).slice(2, 9)}`
let previousFocus = null

function getFocusables() {
  if (!dialogEl.value) return []
  return Array.from(
    dialogEl.value.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    )
  )
}

function onKeydown(e) {
  if (e.key === 'Escape') { emit('close'); return }
  if (e.key !== 'Tab') return
  const focusables = getFocusables()
  if (!focusables.length) { e.preventDefault(); return }
  const first = focusables[0]
  const last = focusables[focusables.length - 1]
  if (e.shiftKey) {
    if (document.activeElement === first) { e.preventDefault(); last.focus() }
  } else {
    if (document.activeElement === last) { e.preventDefault(); first.focus() }
  }
}

onMounted(() => {
  previousFocus = document.activeElement
  document.addEventListener('keydown', onKeydown)
  const focusables = getFocusables()
  if (focusables.length) focusables[0].focus()
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  if (previousFocus && typeof previousFocus.focus === 'function') {
    previousFocus.focus()
  }
})
</script>
