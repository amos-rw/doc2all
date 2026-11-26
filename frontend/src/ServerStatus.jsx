import { useEffect, useState } from 'react'
import { getJson } from './api.js'

const NAMES = { libreoffice: 'LibreOffice', tesseract: 'Tesseract' }

// Shown only while developing: can the page reach the server, and are the programs there?
export default function ServerStatus() {
  const [health, setHealth] = useState(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    getJson('/api/dev/health').then(setHealth, () => setFailed(true))
  }, [])

  if (failed) return <p className="status bad">Cannot reach the server. Is it running on port 8010?</p>
  if (!health) return <p className="status">Looking for the server…</p>
  return (
    <p className="status">
      Server connected
      {Object.entries(health.tools).map(([key, found]) => (
        <span key={key}>
          {NAMES[key]}: {found ? 'found' : 'missing'}
        </span>
      ))}
    </p>
  )
}
