import { computed, ref } from 'vue'
import { useIntervalFn } from '@vueuse/core'
import { isAdmissionError } from '../api/errors'

/** 使用绝对截止时间计算剩余秒数，后台标签页定时器降频时也不会越等越长。 */
export function useRequestCooldown() {
  const now = ref(Date.now())
  const until = ref(0)
  const reason = ref('')
  const { pause, resume } = useIntervalFn(() => {
    now.value = Date.now()
    if (now.value >= until.value) pause()
  }, 250, { immediate: false })
  const remainingSeconds = computed(() => Math.max(0, Math.ceil((until.value - now.value) / 1000)))
  const blocked = computed(() => remainingSeconds.value > 0)

  function handleError(error: unknown): boolean {
    if (!isAdmissionError(error)) return false
    reason.value = error.message
    until.value = Math.max(until.value, Date.now() + (error.retryAfterSeconds ?? 1) * 1000)
    now.value = Date.now()
    resume()
    return true
  }

  return { remainingSeconds, blocked, reason, handleError }
}
