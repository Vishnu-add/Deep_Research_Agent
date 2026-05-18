import { useStorage, createSharedComposable } from '@vueuse/core'
import { ref } from 'vue'
import { $fetch } from 'ofetch'

export interface ModelItem { value: string, label: string, icon: string }

export const useModels = createSharedComposable(() => {
  const models = ref<ModelItem[]>([])
  const model = useStorage<string>('model', 'qwen3:8b')

  const fetchModels = async () => {
    const list = await $fetch<ModelItem[]>('/api/models').catch(() => [] as ModelItem[])
    models.value = list
    if (list.length && !list.some(m => m.value === model.value)) model.value = list[0]!.value
  }

  fetchModels()

  return { models, model, fetchModels }
})
