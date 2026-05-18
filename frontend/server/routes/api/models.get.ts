import { defineHandler } from 'nitro'
import { OLLAMA_URL } from '../../utils/ollama'

const FALLBACK = [{ value: 'qwen3:8b', label: 'qwen3:8b', icon: 'i-simple-icons:ollama' }]
const SKIP = ['bert', 'nomic-bert']

const isEmbed = (m: any): boolean => {
  const f = m?.details?.family
  const fs: string[] = m?.details?.families || []
  if (f && SKIP.includes(f)) return true
  return fs.some(x => SKIP.includes(x) || /bert/i.test(x))
}

export default defineHandler(async () => {
  try {
    const res = await fetch(`${OLLAMA_URL}/api/tags`)
    if (!res.ok) return FALLBACK
    const j: any = await res.json()
    const items = (j?.models || []).filter((m: any) => !isEmbed(m)).map((m: any) => ({ value: m.name, label: m.name, icon: 'i-simple-icons:ollama' }))
    return items.length ? items : FALLBACK
  } catch {
    return FALLBACK
  }
})
