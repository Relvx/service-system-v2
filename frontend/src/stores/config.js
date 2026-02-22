import { defineStore } from 'pinia'
import { ref } from 'vue'
import { configAPI } from '../services/api.js'

export const useConfigStore = defineStore('config', () => {
  const roles = ref([])
  const visitStatuses = ref([])
  const visitTypes = ref([])
  const priorities = ref([])
  const defectStatuses = ref([])
  const defectActionTypes = ref([])
  const attachmentKinds = ref([])
  const purchaseStatuses = ref([])
  const serviceFrequencies = ref([])
  const loaded = ref(false)

  async function loadAll() {
    if (loaded.value) return
    try {
      const [r, vs, vt, p, ds, dat, ak, ps, sf] = await Promise.all([
        configAPI.getRoles(),
        configAPI.getVisitStatuses(),
        configAPI.getVisitTypes(),
        configAPI.getPriorities(),
        configAPI.getDefectStatuses(),
        configAPI.getDefectActionTypes(),
        configAPI.getAttachmentKinds(),
        configAPI.getPurchaseStatuses(),
        configAPI.getServiceFrequencies(),
      ])
      roles.value = r.data
      visitStatuses.value = vs.data
      visitTypes.value = vt.data
      priorities.value = p.data
      defectStatuses.value = ds.data
      defectActionTypes.value = dat.data
      attachmentKinds.value = ak.data
      purchaseStatuses.value = ps.data
      serviceFrequencies.value = sf.data
      loaded.value = true
    } catch (e) {
      console.error('Failed to load config', e)
    }
  }

  function getLabel(list, code, fallback = code) {
    return list.find((i) => i.code === code)?.display_name || fallback
  }

  function getColor(list, code, fallback = 'gray') {
    return list.find((i) => i.code === code)?.color || fallback
  }

  function visitStatusLabel(code) { return getLabel(visitStatuses.value, code) }
  function visitStatusColor(code) { return getColor(visitStatuses.value, code) }
  function visitTypeLabel(code) { return getLabel(visitTypes.value, code) }
  function priorityLabel(code) { return getLabel(priorities.value, code) }
  function priorityColor(code) { return getColor(priorities.value, code) }
  function defectStatusLabel(code) { return getLabel(defectStatuses.value, code) }
  function defectStatusColor(code) { return getColor(defectStatuses.value, code) }
  function defectActionLabel(code) { return getLabel(defectActionTypes.value, code) }
  function purchaseStatusLabel(code) { return getLabel(purchaseStatuses.value, code) }
  function purchaseStatusColor(code) { return getColor(purchaseStatuses.value, code) }
  function serviceFrequencyLabel(code) { return getLabel(serviceFrequencies.value, code) }

  return {
    roles, visitStatuses, visitTypes, priorities,
    defectStatuses, defectActionTypes, attachmentKinds,
    purchaseStatuses, serviceFrequencies, loaded,
    loadAll,
    visitStatusLabel, visitStatusColor, visitTypeLabel,
    priorityLabel, priorityColor,
    defectStatusLabel, defectStatusColor, defectActionLabel,
    purchaseStatusLabel, purchaseStatusColor, serviceFrequencyLabel,
  }
})
