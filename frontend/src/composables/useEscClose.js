import { onMounted, onUnmounted } from 'vue'

/**
 * Closes the topmost open modal when ESC is pressed.
 * @param {Array<{ isOpen: () => boolean, close: () => void }>} modals
 *   Array of modal descriptors ordered from lowest to highest priority.
 *   The last one that isOpen() === true will be closed.
 */
export function useEscClose(modals) {
  function onKeydown(e) {
    if (e.key !== 'Escape') return
    // Find the last open modal (topmost)
    for (let i = modals.length - 1; i >= 0; i--) {
      if (modals[i].isOpen()) {
        modals[i].close()
        return
      }
    }
  }

  onMounted(() => window.addEventListener('keydown', onKeydown))
  onUnmounted(() => window.removeEventListener('keydown', onKeydown))
}
