export const timeLeft = (at) => {
  const minutes = Math.max(0, Math.round((at - Date.now()) / 60_000))
  return minutes >= 60 ? `${Math.round(minutes / 60)} h` : `${minutes} min`
}

export const dayAndTime = (at) => new Date(at).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
export const day = (at) => new Date(at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
export const clock = (at) => new Date(at).toLocaleTimeString('en-GB')

export const ago = (at) => {
  const minutes = Math.max(0, Math.round((Date.now() - at) / 60_000))
  if (minutes < 2) return 'just now'
  if (minutes < 60) return `${minutes} minutes ago`
  if (minutes < 60 * 24) return `${Math.round(minutes / 60)} hours ago`
  return day(at)
}

export const size = (bytes) => (bytes > 1_048_576 ? `${(bytes / 1_048_576).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`)

export function saveBlob(blob, name) {
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = name
  link.click()
  setTimeout(() => URL.revokeObjectURL(link.href), 1000)
}

export const readCookie = (name) => new RegExp(`(?:^|; )${name}=([^;]*)`).exec(document.cookie)?.[1]
export const writeCookie = (name, value) => (document.cookie = `${name}=${value}; path=/; max-age=31536000; SameSite=Lax`)

export const readTheme = () => readCookie('theme') || 'auto'
export function applyTheme(theme) {
  if (theme === 'auto') delete document.documentElement.dataset.theme
  else document.documentElement.dataset.theme = theme
  writeCookie('theme', theme)
}

// One short sound when a job finishes (NFR-11). Made by the browser, so there is no file to load.
export function playDone() {
  try {
    const audio = new AudioContext()
    for (const [delay, frequency] of [[0, 660], [0.13, 990]]) {
      const tone = audio.createOscillator()
      const volume = audio.createGain()
      tone.frequency.value = frequency
      volume.gain.setValueAtTime(0.0001, audio.currentTime + delay)
      volume.gain.exponentialRampToValueAtTime(0.12, audio.currentTime + delay + 0.02)
      volume.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + delay + 0.28)
      tone.connect(volume).connect(audio.destination)
      tone.start(audio.currentTime + delay)
      tone.stop(audio.currentTime + delay + 0.3)
    }
    setTimeout(() => audio.close(), 800)
  } catch {
    // no sound on this device: the screen shows the same news
  }
}
