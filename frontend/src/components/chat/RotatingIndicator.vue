<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import { useIntervalFn, useMediaQuery } from '@vueuse/core'

const words = ['Cooking', 'Buzzing', 'Pondering', 'Brewing', 'Hatching', 'Spinning', 'Whisking', 'Tinkering', 'Mulling', 'Conjuring', 'Doodling', 'Crunching']
const i = ref(0)
const reduced = useMediaQuery('(prefers-reduced-motion: reduce)')
const { pause, resume } = useIntervalFn(() => { i.value = (i.value + 1) % words.length }, 2000, { immediate: false })

watchEffect(() => { if (reduced.value) { pause(); i.value = 0 } else resume() })
</script>

<template>
  <UChatShimmer
    v-bind="$attrs"
    :text="`${words[i]}…`"
  />
</template>
