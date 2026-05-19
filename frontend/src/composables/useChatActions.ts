import { defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { $fetch } from 'ofetch'
import { useChats } from './useChats'
import { useCsrf } from './useCsrf'

const ModalRename = defineAsyncComponent(() => import('../components/ModalRename.vue'))
const ModalConfirm = defineAsyncComponent(() => import('../components/ModalConfirm.vue'))

export function useChatActions() {
  const route = useRoute()
  const router = useRouter()
  const toast = useToast()
  const overlay = useOverlay()
  const { csrf, headerName } = useCsrf()
  const { updateChat, removeChat } = useChats()

  const renameModal = overlay.create(ModalRename)
  const deleteModal = overlay.create(ModalConfirm, {
    props: {
      title: 'Delete chat',
      description: 'Are you sure you want to delete this chat? This cannot be undone.',
      color: 'error'
    }
  })
  const deleteBelowModal = overlay.create(ModalConfirm, {
    props: {
      title: 'Delete chats below',
      description: 'Delete every chat below this one? This cannot be undone.',
      color: 'error'
    }
  })

  async function renameChat(id: string, currentTitle?: string | null): Promise<string | null> {
    const instance = renameModal.open({ title: currentTitle ?? '' })
    const result = await instance.result

    if (!result || result === currentTitle) return null

    try {
      await $fetch(`/api/chats/title/${id}`, {
        method: 'PATCH',
        headers: { [headerName]: csrf() },
        body: { title: result }
      })

      updateChat(id, { label: result })

      return result
    } catch {
      toast.add({
        description: 'Failed to rename chat',
        icon: 'i-lucide-alert-circle',
        color: 'error'
      })

      return null
    }
  }

  async function deleteChat(id: string): Promise<boolean> {
    const instance = deleteModal.open()
    const result = await instance.result

    if (!result) return false

    try {
      await $fetch(`/api/chats/${id}`, {
        method: 'DELETE',
        headers: { [headerName]: csrf() }
      })

      toast.add({
        title: 'Chat deleted',
        description: 'Your chat has been deleted',
        icon: 'i-lucide-trash'
      })

      removeChat(id)

      if ((route.params as { id?: string }).id === id) {
        router.push('/')
      }

      return true
    } catch {
      toast.add({
        description: 'Failed to delete chat',
        icon: 'i-lucide-alert-circle',
        color: 'error'
      })

      return false
    }
  }

  async function deleteChatsBelow(ids: string[]): Promise<boolean> {
    if (!ids.length) return false

    const instance = deleteBelowModal.open()
    const result = await instance.result

    if (!result) return false

    const currentId = (route.params as { id?: string }).id
    try {
      await Promise.all(ids.map(id => $fetch(`/api/chats/${id}`, {
        method: 'DELETE',
        headers: { [headerName]: csrf() }
      })))

      ids.forEach(id => removeChat(id))

      toast.add({
        title: 'Chats deleted',
        description: `${ids.length} chat${ids.length > 1 ? 's' : ''} deleted`,
        icon: 'i-lucide-trash'
      })

      if (currentId && ids.includes(currentId)) {
        router.push('/')
      }

      return true
    } catch {
      toast.add({
        description: 'Failed to delete chats',
        icon: 'i-lucide-alert-circle',
        color: 'error'
      })

      return false
    }
  }

  return {
    renameChat,
    deleteChat,
    deleteChatsBelow
  }
}
