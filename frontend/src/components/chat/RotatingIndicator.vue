<script setup lang="ts">
import { ref } from 'vue'
import { useIntervalFn } from '@vueuse/core'

const words = ['Cooking', 'Buzzing', 'Pondering', 'Brewing', 'Hatching', 'Spinning', 'Whisking', 'Tinkering', 'Mulling', 'Conjuring', 'Doodling', 'Crunching']
const i = ref(0)

useIntervalFn(() => { i.value = (i.value + 1) % words.length }, 2000)
</script>

<template>
  <UChatShimmer
    v-bind="$attrs"
    :text="`${words[i]}…`"
  />
</template>
