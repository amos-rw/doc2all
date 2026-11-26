// Some changes need the second step again. Run the change; if the server says "confirm", ask, then run it again.
import { createContext, useCallback, useContext, useState } from 'react'
import { api } from '../api/calls.js'
import { usePasskeyOnDevice } from '../api/passkey.js'
import { ApiError } from '../api/errors.js'
import { Alert, CodeInput, DemoHint, Dialog, Icon, useAction } from '../components/ui.jsx'
import { useSession } from './session.jsx'

const ConfirmContext = createContext(null)
export const useConfirm = () => useContext(ConfirmContext)

export function ConfirmProvider({ children }) {
  const [asking, setAsking] = useState(null)

  const confirmed = useCallback(async (why, action) => {
    try {
      return await action()
    } catch (error) {
      if (error.code !== 'confirm') throw error
      await new Promise((resolve, reject) => setAsking({ why, resolve, reject }))
      return action()
    }
  }, [])

  const done = () => {
    asking.resolve()
    setAsking(null)
  }
  const cancel = () => {
    asking.reject(new ApiError(0, 'cancelled', 'Cancelled.'))
    setAsking(null)
  }

  return (
    <ConfirmContext.Provider value={confirmed}>
      {children}
      {asking && <ConfirmDialog why={asking.why} onDone={done} onCancel={cancel} />}
    </ConfirmContext.Provider>
  )
}

function ConfirmDialog({ why, onDone, onCancel }) {
  const { session } = useSession()
  const [byCode, setByCode] = useState(false)
  const [code, setCode] = useState('')
  const [busy, error, run] = useAction()

  const usePasskey = () =>
    run(async () => {
      const { challenge } = await api.passkeyOptions()
      const answer = await usePasskeyOnDevice(challenge)
      await api.confirm({ method: 'passkey', challenge, answer })
      onDone()
    })
  const askCode = () =>
    run(async () => {
      await api.sendCode()
      setByCode(true)
    })
  const useCode = (event) => {
    event.preventDefault()
    run(async () => {
      await api.confirm({ method: 'code', code })
      onDone()
    })
  }

  return (
    <Dialog mood="checking" title="Confirm it is you" sub={why} onClose={onCancel}>
      {error && <Alert>{error}</Alert>}
      {byCode ? (
        <form className="stack" onSubmit={useCode}>
          <span className="note">Enter the code sent to {session.emailMasked}.</span>
          <CodeInput value={code} onChange={setCode} />
          <DemoHint>The code is 123456.</DemoHint>
          <button className="mbtn" disabled={busy || code.length < 6}>
            Confirm
          </button>
        </form>
      ) : (
        <>
          {session.methods.passkey && (
            <button className="bigkey" onClick={usePasskey} disabled={busy}>
              <span className="ic">{Icon.key}</span>
              <span>
                <b>{busy ? 'Confirm on your device…' : 'Use my passkey'}</b>
                <span>Fingerprint, face, PIN or security key</span>
              </span>
            </button>
          )}
          {session.methods.emailCode && (
            <button className="mbtn ghost" onClick={askCode} disabled={busy}>
              Email me a code
            </button>
          )}
        </>
      )}
      <button className="link center" onClick={onCancel}>
        Cancel
      </button>
    </Dialog>
  )
}
