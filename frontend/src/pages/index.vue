<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { $fetch } from 'ofetch'
import { useChats } from '../composables/useChats'
import { useCsrf } from '../composables/useCsrf'
import { useUserSession } from '../composables/useUserSession'
import Navbar from '../components/Navbar.vue'

const { fetchChats } = useChats()
const { csrf, headerName } = useCsrf()
const { user } = useUserSession()
const input = ref('')
const loading = ref(false)
const router = useRouter()

const G = {
  en: { morning: 'Good morning', afternoon: 'Good afternoon', evening: 'Good evening' },
  fr: { morning: 'Bonjour', afternoon: 'Bon après-midi', evening: 'Bonsoir' }
} as const

const greeting = computed(() => {
  const h = new Date().getHours()
  const p = h < 12 ? 'morning' : h < 18 ? 'afternoon' : 'evening'
  const lang = (document.documentElement.lang || 'en').toLowerCase().startsWith('fr') ? 'fr' : 'en'
  const t = G[lang][p]
  const name = user.value?.name?.split(' ')[0] || user.value?.username
  return name ? `${t}, ${name}` : t
})

async function createChat(prompt: string) {
  input.value = prompt
  loading.value = true
  const chat = await $fetch('/api/chats', {
    method: 'POST',
    headers: { [headerName]: csrf() },
    body: { input: prompt }
  })

  await fetchChats()
  router.push(`/chat/${chat?.id}`)
}

function onSubmit() {
  createChat(input.value)
}

const quickChats = [
  {
    label: 'What is photosynthesis?',
    icon: 'i-lucide-leaf'
  },
  {
    label: 'How does HTTP work?',
    icon: 'i-lucide-globe'
  },
  {
    label: 'Who painted the Mona Lisa?',
    icon: 'i-lucide-palette'
  },
  {
    label: 'What is machine learning?',
    icon: 'i-lucide-brain'
  },
  {
    label: 'What causes auroras?',
    icon: 'i-lucide-sparkles'
  },
  {
    label: 'Why is the sky blue?',
    icon: 'i-lucide-cloud'
  }
]
</script>

<template>
  <UDashboardPanel
    id="home"
    class="min-h-0"
    :ui="{ body: 'p-0 sm:p-0' }"
  >
    <template #header>
      <Navbar />
    </template>

    <template #body>
      <UContainer class="flex-1 flex flex-col justify-center gap-4 sm:gap-6 py-8">
        <h1 class="text-3xl sm:text-4xl text-highlighted font-bold">
          {{ greeting }}
        </h1>

        <UChatPrompt
          v-model="input"
          :status="loading ? 'streaming' : 'ready'"
          class="[view-transition-name:chat-prompt]"
          variant="subtle"
          :ui="{ base: 'px-1.5' }"
          @submit="onSubmit"
        >
          <template #footer>
            <ModelSelect />

            <UChatPromptSubmit
              color="neutral"
              size="sm"
            />
          </template>
        </UChatPrompt>

        <div class="flex flex-wrap gap-2">
          <UButton
            v-for="quickChat in quickChats"
            :key="quickChat.label"
            :icon="quickChat.icon"
            :label="quickChat.label"
            size="sm"
            color="neutral"
            variant="outline"
            class="rounded-full"
            @click="createChat(quickChat.label)"
          />
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
