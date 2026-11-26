// A helper for looking at every state while there is no real server. It is not part of Doc2All.
import { useState } from 'react'
import { api } from '../api/calls.js'
import { realFiles } from '../api/client.js'
import { useSession } from '../state/session.jsx'

export default function DemoPanel() {
  const [open, setOpen] = useState(false)
  const { refresh, session } = useSession()

  const demo = async (change) => {
    if (import.meta.env.VITE_API !== 'server') {
      const state = await import('../api/mock/state.js')
      change(state)
    }
  }
  const idle = async () => {
    await demo((s) => s.passTime(31 * s.MINUTE))
    if (session.state === 'signed_in') await api.notices().catch(() => {})
    else await refresh()
  }
  const notice = async () => {
    await demo((s) => s.addSecurityNotice())
    window.location.reload()
  }
  const startAgain = async () => {
    await demo((s) => s.reset())
    document.cookie = 'cookie_ok=; path=/; max-age=0'
    window.location.assign('/')
  }

  return (
    <aside className="demo" aria-label="Demo helper">
      {open && (
        <div className="demo-box">
          <b>{realFiles ? 'Partly demo data' : 'Demo data only'}</b>
          <span>
            {realFiles
              ? 'Upload, convert and History use the server. The rest is made up and stays in this browser tab.'
              : 'Nothing is sent or converted. It stays in this browser tab.'}
          </span>
          <span>
            User <code>amos@example.com</code>
            <br />
            Admin <code>admin@example.com</code>
            <br />
            Password <code>doc2all-demo-pass</code>
            <br />
            Every code <code>123456</code>
          </span>
          <button onClick={idle}>30 minutes pass</button>
          <button onClick={() => demo((s) => s.passTime(6 * s.MINUTE))}>6 minutes pass</button>
          <button onClick={notice}>Add a security notice</button>
          <button onClick={startAgain}>Start the demo again</button>
        </div>
      )}
      <button className="demo-tab" aria-expanded={open} onClick={() => setOpen(!open)}>
        {open ? 'Close' : 'Demo'}
      </button>
    </aside>
  )
}
