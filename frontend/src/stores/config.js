import { defineStore } from 'pinia'
import { ref } from 'vue'
import { configAPI } from '../services/api.js'

export const useConfigStore = defineStore('config', () => {
  const visitStatuses = ref([])
  const visitTypes = ref([])
  const priorities = ref([])
  const defectStatuses = ref([])
  const defectActionTypes = ref([])
  const attachmentKinds = ref([])
  const purchaseStatuses = ref([])
  const serviceFrequencies = ref([])
  const permissionGroups = ref([])
  const loaded = ref(false)

  async function loadAll() {
    if (loaded.value) return
    try {
      const [vs, vt, p, ds, dat, ak, ps, sf] = await Promise.all([
        configAPI.getVisitStatuses(),
        configAPI.getVisitTypes(),
        configAPI.getPriorities(),
        configAPI.getDefectStatuses(),
        configAPI.getDefectActionTypes(),
        configAPI.getAttachmentKinds(),
        configAPI.getPurchaseStatuses(),
        configAPI.getServiceFrequencies(),
      ])
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

  function getLabel(list, sysname, fallback = sysname) {
    return list.find((i) => i.sysname === sysname)?.display_name || fallback
  }

  function visitStatusLabel(sysname) { return getLabel(visitStatuses.value, sysname) }
  function visitTypeLabel(sysname) { return getLabel(visitTypes.value, sysname) }
  function priorityLabel(sysname) { return getLabel(priorities.value, sysname) }
  function defectStatusLabel(sysname) { return getLabel(defectStatuses.value, sysname) }
  function defectActionLabel(sysname) { return getLabel(defectActionTypes.value, sysname) }
  function purchaseStatusLabel(sysname) { return getLabel(purchaseStatuses.value, sysname) }
  function serviceFrequencyLabel(sysname) { return getLabel(serviceFrequencies.value, sysname) }

  return {
    visitStatuses, visitTypes, priorities,
    defectStatuses, defectActionTypes, attachmentKinds,
    purchaseStatuses, serviceFrequencies, permissionGroups, loaded,
    loadAll,
    visitStatusLabel, visitTypeLabel,
    priorityLabel,
    defectStatusLabel, defectActionLabel,
    purchaseStatusLabel, serviceFrequencyLabel,
  }
})
