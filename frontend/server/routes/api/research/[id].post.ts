import type { UIMessage } from 'ai'
import { createUIMessageStream, createUIMessageStreamResponse } from 'ai'
import { z } from 'zod'
import { useUserSession } from '../../../utils/session'
import { useDrizzle, tables, eq, and } from '../../../utils/drizzle'
import { defineHandler, HTTPError } from 'nitro'
import { getValidatedRouterParams, readValidatedBody } from 'nitro/h3'
import { OLLAMA_URL } from '../../../utils/ollama'

const BACKEND_URL = process.env.RESEARCH_BACKEND_URL || 'http://localhost:8001/get_stream'
const TITLE_MODEL = process.env.OLLAMA_TITLE_MODEL || 'qwen3:8b'
const MAX_ITER = 3

const REFUSAL = /^(as my|as of|i cannot|i can't|i am unable|i'm unable|i'm sorry|sorry|i don't|i do not|here is|here's|the title|sure|certainly|of course)/i

async function genTitle(msg: string): Promise<string> {
  const fallback = msg.split('\n')[0].trim().slice(0, 28).replace(/["':]/g, '')
  try {
    const res = await fetch(`${OLLAMA_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: TITLE_MODEL,
        messages: [
          { role: 'system', content: '/no_think You output a chat title only. Never answer the user. Never include "As", "I", "Sorry", quotes, colons, markdown, or any prefix. Reply with 2 to 5 words summarising the user message, nothing else.' },
          { role: 'user', content: msg }
        ],
        stream: false
      })
    })
    if (!res.ok) return fallback
    const j: any = await res.json()
    const first = (j?.message?.content || '').replace(/<think>[\s\S]*?<\/think>/g, '').trim().split('\n')[0].trim()
    if (!first || REFUSAL.test(first)) return fallback
    return first.slice(0, 30).replace(/["':\n]/g, '') || fallback
  } catch {
    return fallback
  }
}

function extractObjects(buf: string): { objs: string[], rest: string } {
  const objs: string[] = []
  let i = 0, depth = 0, start = -1, inStr = false, esc = false
  while (i < buf.length) {
    const c = buf[i]
    if (inStr) {
      if (esc) esc = false
      else if (c === '\\') esc = true
      else if (c === '"') inStr = false
    } else {
      if (c === '"') inStr = true
      else if (c === '{') { if (depth === 0) start = i; depth++ }
      else if (c === '}') { depth--; if (depth === 0 && start >= 0) { objs.push(buf.slice(start, i + 1)); start = -1 } }
    }
    i++
  }
  const rest = depth > 0 && start >= 0 ? buf.slice(start) : (start === -1 ? '' : buf.slice(start))
  return { objs, rest }
}

function lastUserText(msgs: UIMessage[]): string {
  for (let i = msgs.length - 1; i >= 0; i--) {
    const m = msgs[i]
    if (m?.role === 'user') return (m.parts || []).filter((p: any) => p.type === 'text').map((p: any) => p.text).join('\n')
  }
  return ''
}

export default defineHandler(async (event) => {
  const session = await useUserSession(event)
  const { id } = await getValidatedRouterParams(event, z.object({ id: z.string() }).parse)
  const { messages, session_id, model } = await readValidatedBody(event, z.object({
    messages: z.array(z.custom<UIMessage>()),
    session_id: z.string().optional(),
    model: z.string().optional()
  }).parse)

  const db = useDrizzle()
  const chat = await db.query.chats.findFirst({
    where: (c, { eq }) => and(eq(c.id, id), eq(c.userId, session.data.user?.id || session.id!)),
    with: { messages: true }
  })
  if (!chat) throw new HTTPError({ statusCode: 404, statusMessage: 'Chat not found' })

  const titleP: Promise<string> | null = chat.title ? null : (async () => {
    const first = (messages[0]?.parts || []).filter((p: any) => p.type === 'text').map((p: any) => p.text).join('\n')
    const t = await genTitle(first)
    await db.update(tables.chats).set({ title: t }).where(eq(tables.chats.id, id))
    return t
  })()

  const last = messages[messages.length - 1]
  if (last?.role === 'user' && messages.length > 1) {
    await db.insert(tables.messages).values({
      id: last.id,
      chatId: id,
      role: 'user',
      parts: last.parts
    }).onConflictDoUpdate({ target: tables.messages.id, set: { parts: last.parts } })
  }

  const q = lastUserText(messages)
  const sid = session_id ?? id

  const stream = createUIMessageStream({
    originalMessages: messages,
    execute: async ({ writer }) => {
      const rid = crypto.randomUUID()
      const tid = crypto.randomUUID()
      let rOpen = false, tOpen = false
      writer.write({ type: 'start' })
      if (titleP) titleP.then(t => { try { writer.write({ type: 'data-chat-title', data: { message: t }, transient: true }) } catch {} }).catch(() => {})
      try {
        const res = await fetch(BACKEND_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q, max_iterations: MAX_ITER, session_id: sid, model }),
          signal: event.req.signal
        })
        if (!res.ok || !res.body) throw new Error(`Backend ${res.status}`)
        const reader = res.body.getReader()
        const dec = new TextDecoder()
        let buf = ''
        const handle = (type: string, desc: string) => {
          if (type === 'thinking') {
            if (!rOpen) { writer.write({ type: 'reasoning-start', id: rid }); rOpen = true }
            writer.write({ type: 'reasoning-delta', id: rid, delta: desc + '\n' })
          } else if (type === 'final_answer') {
            if (rOpen) { writer.write({ type: 'reasoning-end', id: rid }); rOpen = false }
            if (!tOpen) { writer.write({ type: 'text-start', id: tid }); tOpen = true }
            writer.write({ type: 'text-delta', id: tid, delta: desc })
          }
        }
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buf += dec.decode(value, { stream: true })
          if (buf.includes('{')) {
            const { objs, rest } = extractObjects(buf)
            buf = rest
            for (const s of objs) {
              try {
                const o = JSON.parse(s)
                if (o && typeof o.type === 'string' && typeof o.description === 'string') handle(o.type, o.description)
              } catch {
                handle('thinking', s)
              }
            }
          } else {
            const txt = buf.trim()
            if (txt) handle('thinking', txt)
            buf = ''
          }
        }
        buf += dec.decode()
        if (buf.trim()) {
          const { objs } = extractObjects(buf)
          for (const s of objs) {
            try {
              const o = JSON.parse(s)
              if (o && typeof o.type === 'string' && typeof o.description === 'string') handle(o.type, o.description)
            } catch {}
          }
        }
        if (rOpen) { writer.write({ type: 'reasoning-end', id: rid }); rOpen = false }
        if (tOpen) { writer.write({ type: 'text-end', id: tid }); tOpen = false }
      } catch (e: any) {
        if (rOpen) { writer.write({ type: 'reasoning-end', id: rid }); rOpen = false }
        if (!tOpen) { writer.write({ type: 'text-start', id: tid }); tOpen = true }
        writer.write({ type: 'text-delta', id: tid, delta: `Error: ${e?.message || 'stream failed'}` })
        writer.write({ type: 'text-end', id: tid })
      }
      writer.write({ type: 'finish' })
    },
    onFinish: async ({ messages: ms }) => {
      await db.insert(tables.messages).values(ms.map(m => ({
        id: m.id,
        chatId: chat.id,
        role: m.role as 'user' | 'assistant',
        parts: m.parts
      }))).onConflictDoNothing()
    }
  })

  return createUIMessageStreamResponse({ stream })
})
