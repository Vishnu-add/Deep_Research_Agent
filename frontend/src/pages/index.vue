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
  fr: { morning: 'Bonjour', afternoon: 'Bon après-midi', evening: 'Bonsoir' },
  no: { morning: 'God morgen', afternoon: 'God ettermiddag', evening: 'God kveld' },
  hi: { morning: 'सुप्रभात', afternoon: 'नमस्ते', evening: 'शुभ संध्या' }
} as const

const greeting = computed(() => {
  const h = new Date().getHours()
  const p = h < 12 ? 'morning' : h < 18 ? 'afternoon' : 'evening'
  const docLang = (document.documentElement.lang || 'en').toLowerCase()
  const lang = docLang.startsWith('fr') ? 'fr'
    : docLang.startsWith('no') || docLang.startsWith('nb') || docLang.startsWith('nn') ? 'no'
    : docLang.startsWith('hi') ? 'hi'
    : 'en'
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
    label: 'Test-Time vs Pre-training Scaling',
    icon: 'i-lucide-cpu',
    prompt: 'Investigate the performance-to-compute efficiency of Test-Time Scaling (System 2 thinking) versus traditional Pre-training Scaling Laws. Specifically, compare the cost-effectiveness of DeepSeek-R1\'s reinforcement learning approach against OpenAI o3\'s reasoning tiers for mathematical reasoning tasks.'
  },
  {
    label: 'Lost-in-the-Middle in Long-Context Models',
    icon: 'i-lucide-search',
    prompt: 'Analyze the \'Lost-in-the-Middle\' phenomenon in 2026\'s ultra-long context models (1M+ tokens). Compare the retrieval accuracy of Meta Llama 4 Scout (10M token window) against hybrid Mamba-Transformer (Jamba) architectures.'
  },
  {
    label: 'Early vs Late Fusion in VLMs',
    icon: 'i-lucide-eye',
    prompt: 'Evaluate the shift from Late Fusion to Early Fusion in 2026 Vision-Language Models (VLMs). Compare the visual grounding capabilities of Gemini 2.5 Pro and InternVL3-78B on the MMMU (Massive Multi-discipline Multimodal Understanding) benchmark.'
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
            @click="createChat(quickChat.prompt ?? quickChat.label)"
          />
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
