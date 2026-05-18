<script setup lang="ts">
import { computed } from 'vue'
import ReasoningComark from './ReasoningComark'

const props = defineProps<{ text: string, streaming: boolean }>()

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

const html = computed(() => {
  const ls = props.text.split('\n').map(l => l.trim()).filter(Boolean)
  const last = ls.length - 1
  return ls.map((l, i) => `<step type="${i === last && props.streaming ? 'current' : 'done'}">${esc(l)}</step>`).join('')
})
</script>

<template>
  <ReasoningComark
    :markdown="html"
    :streaming="streaming"
  />
</template>
