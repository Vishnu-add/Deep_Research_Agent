import { defineComarkComponent } from '@comark/vue'
import ReasoningStep from './ReasoningStep.vue'

export default defineComarkComponent({
  name: 'ReasoningComark',
  components: { step: ReasoningStep },
  class: 'not-prose flex flex-col gap-1.5 text-sm w-full min-w-0'
})
