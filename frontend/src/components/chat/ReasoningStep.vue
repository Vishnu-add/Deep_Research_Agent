<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ type?: string }>()
const current = computed(() => props.type === 'current')
</script>

<template>
  <div class="grid grid-cols-[1rem_1fr] gap-2 items-start w-full min-w-0">
    <UIcon
      :name="current ? 'i-lucide-loader-circle' : 'i-lucide-check'"
      :class="['mt-0.5 size-4', current ? 'text-primary animate-spin' : 'text-muted']"
    />
    <span :class="['break-words whitespace-normal min-w-0', current ? 'text-highlighted font-medium' : 'text-muted']">
      <slot />
    </span>
  </div>
</template>
