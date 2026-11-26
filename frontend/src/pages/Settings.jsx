// Screen 10: Settings. Security changes ask for the second step again.
import { useCallback, useEffect, useState } from 'react'
import { Link, NavLink, Navigate, useLocation, useParams } from 'react-router'
import { api } from '../api/calls.js'
import { createPasskeyOnDevice } from '../api/passkey.js'
import { useRefreshNotices } from '../components/Layout.jsx'
import { Alert, CodeInput, Corner, DemoHint, Dialog, Field, Icon, Pill, Strength, Toggle, useAction } from '../components/ui.jsx'
import { ago, day, playDone } from '../lib/helpers.js'
import { useConfirm } from '../state/confirm.jsx'
import { useSession } from '../state/session.jsx'

const TABS = { security: 'Security', privacy: 'Privacy', notifications: 'Notifications', about: 'About' }

export default function Settings() {
  const { tab = 'security' } = useParams()
  const { session, refresh } = useSession()
  const [me, setMe] = useState(null)
  const [busy, error, run] = useAction()
  const refreshNotices = useRefreshNotices()

  const load = useCallback(async () => setMe(await api.me()), [])
  useEffect(() => {
    run(load)
  }, [load]) // eslint-disable-line react-hooks/exhaustive-deps

  // Run a change, then show the new state.
  const change = (action) =>
    run(async () => {
      await action()
      await Promise.all([load(), refresh()])
      refreshNotices()
    })

  if (!TABS[tab]) return <Navigate to="/settings/security" replace />
  const Tab = { security: Security, privacy: Privacy, notifications: Notifications, about: About }[tab]

  return (
    <>
      <div>
        <h1 className="m-h">Settings</h1>
        <span className="m-sub">Security changes ask for your second step. It counts for 5 minutes.</span>
      </div>
      <nav className="tabs" aria-label="Settings">
        {Object.entries(TABS)
          .filter(([key]) => session.role !== 'admin' || key !== 'notifications')
          .map(([key, label]) => (
            <NavLink key={key} to={`/settings/${key}`} className={() => (key === tab ? 'on' : '')}>
              {label}
            </NavLink>
          ))}
      </nav>
      {error && <Alert>{error}</Alert>}
      {me && <Tab me={me} change={change} busy={busy} reload={load} />}
      {tab === 'security' && <Corner>Add a passkey on each device.</Corner>}
    </>
  )
}

function Security({ me, change, busy, reload }) {
  const confirmed = useConfirm()
  const wantsPassword = useLocation().state?.changePassword
  const [dialog, setDialog] = useState(wantsPassword ? 'password' : null)
  const refreshNotices = useRefreshNotices()
  const close = () => setDialog(null)
  const finished = () => {
    close()
    reload()
    refreshNotices()
  }

  const removePasskey = (key) => change(() => confirmed(`Before I remove the passkey "${key.name}".`, () => api.removePasskey(key.id)))
  const setCodes = (allowed) => change(() => confirmed(`Before I switch email codes ${allowed ? 'on' : 'off'}.`, () => api.setEmailCode(allowed)))

  return (
    <>
      <section className="card">
        <div className="rowx">
          <div>
            <b>Passkeys</b>
            <div className="note">The safest way to sign in.</div>
          </div>
          <button className="mbtn sm" onClick={() => setDialog('passkey')}>
            Add a passkey
          </button>
        </div>
        {me.passkeys.length === 0 && <span className="note">No passkey yet.</span>}
        {me.passkeys.map((key) => (
          <div key={key.id} className="rowx">
            <div>
              <span className="keyicon">{Icon.key}</span> {key.name} <span className="note">added {day(key.addedAt)}</span>
            </div>
            <button className="mbtn sm ghost" disabled={busy} onClick={() => removePasskey(key)} aria-label={`Remove ${key.name}`}>
              Remove
            </button>
          </div>
        ))}
        <div className="rowx">
          <div>
            <b>Email code</b> <span className="note">as a backup</span>
            <div className="note">Can be switched off while you have two passkeys.</div>
          </div>
          <Toggle label="Email code" on={me.emailCode} disabled={busy} onChange={setCodes} />
        </div>
      </section>
      <section className="card">
        <div className="rowx">
          <div>
            <b>Email</b>
            <div className="note">{me.email}</div>
          </div>
          <button className="mbtn sm ghost" onClick={() => setDialog('email')} aria-label="Change email">
            Change
          </button>
        </div>
        <div className="rowx">
          <div>
            <b>Password</b>
            <div className="note">Changed {ago(me.passwordChangedAt)}</div>
          </div>
          <button className="mbtn sm ghost" onClick={() => setDialog('password')} aria-label="Change password">
            Change
          </button>
        </div>
      </section>
      <section className="card">
        <b>Signed in on</b>
        {me.sessions.map((s) => (
          <div key={s.id} className="rowx">
            <div>
              {s.device} {s.current ? <Pill tone="ok">Now</Pill> : <span className="note">{ago(s.lastSeenAt)}</span>}
            </div>
            {!s.current && (
              <button className="mbtn sm ghost" disabled={busy} onClick={() => change(() => api.signOutDevice(s.id))}>
                Sign out
              </button>
            )}
          </div>
        ))}
      </section>
      {dialog === 'passkey' && <AddPasskey onClose={close} onDone={finished} />}
      {dialog === 'password' && <ChangePassword onClose={close} onDone={finished} />}
      {dialog === 'email' && <ChangeEmail onClose={close} onDone={finished} />}
    </>
  )
}

function AddPasskey({ onClose, onDone }) {
  const confirmed = useConfirm()
  const [name, setName] = useState('')
  const [busy, error, run] = useAction()
  const submit = (event) => {
    event.preventDefault()
    run(async () => {
      await confirmed('Before I add a new passkey.', async () => {
        const { challenge } = await api.newPasskeyOptions()
        const answer = await createPasskeyOnDevice(challenge)
        return api.addPasskey(challenge, answer, name)
      })
      onDone()
    })
  }
  return (
    <Dialog title="Add a passkey" sub="Give it a name you will recognise." onClose={onClose}>
      {error && <Alert>{error}</Alert>}
      <form className="stack" onSubmit={submit}>
        <Field label="Name" required maxLength={40} placeholder="For example Phone" value={name} onChange={setName} />
        <div className="pair">
          <button className="mbtn" disabled={busy || !name.trim()}>
            {busy ? 'Confirm on your device…' : 'Add it'}
          </button>
          <button type="button" className="mbtn ghost" onClick={onClose}>
            Cancel
          </button>
        </div>
      </form>
    </Dialog>
  )
}

function ChangePassword({ onClose, onDone }) {
  const confirmed = useConfirm()
  const [password, setPassword] = useState('')
  const [busy, error, run] = useAction()
  const submit = (event) => {
    event.preventDefault()
    run(async () => {
      await confirmed('Before I change your password.', () => api.changePassword(password))
      onDone()
    })
  }
  return (
    <Dialog title="Choose a new password" sub="Your other devices will be signed out." onClose={onClose}>
      {error && <Alert>{error}</Alert>}
      <form className="stack" onSubmit={submit}>
        <Field label="New password" type="password" autoComplete="new-password" value={password} onChange={setPassword} />
        <Strength password={password} />
        <div className="pair">
          <button className="mbtn" disabled={busy || password.length < 12}>
            Save password
          </button>
          <button type="button" className="mbtn ghost" onClick={onClose}>
            Cancel
          </button>
        </div>
      </form>
    </Dialog>
  )
}

function ChangeEmail({ onClose, onDone }) {
  const confirmed = useConfirm()
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [sent, setSent] = useState(false)
  const [busy, error, run] = useAction()
  const submit = (event) => {
    event.preventDefault()
    run(async () => {
      if (!sent) {
        await confirmed('Before I change your email.', () => api.changeEmail(email))
        setSent(true)
        return
      }
      await confirmed('Before I change your email.', () => api.confirmEmail(code))
      onDone()
    })
  }
  return (
    <Dialog title="Change your email" sub={sent ? `Enter the code sent to ${email}.` : 'I send a code to the new address.'} onClose={onClose}>
      {error && <Alert>{error}</Alert>}
      <form className="stack" onSubmit={submit}>
        {sent ? (
          <>
            <CodeInput value={code} onChange={setCode} />
            <DemoHint>the code is 123456.</DemoHint>
          </>
        ) : (
          <Field label="New email" type="email" required value={email} onChange={setEmail} />
        )}
        <div className="pair">
          <button className="mbtn" disabled={busy || (sent ? code.length < 6 : !email)}>
            {sent ? 'Confirm' : 'Send the code'}
          </button>
          <button type="button" className="mbtn ghost" onClick={onClose}>
            Cancel
          </button>
        </div>
      </form>
    </Dialog>
  )
}

function Privacy() {
  const confirmed = useConfirm()
  const { setSession } = useSession()
  const [asking, setAsking] = useState(false)
  const [busy, error, run] = useAction()
  const remove = () =>
    run(async () => {
      await confirmed('Before I delete your account.', () => api.deleteAccount())
      // The message travels with the new session: the sign-in page appears as soon as the session changes.
      setSession({ ...(await api.session()), message: 'Your account was deleted. We sent you an email.' })
    })
  return (
    <>
      <section className="card">
        <b>What we keep</b>
        <Row title="Your files and results" detail="Deleted after 24 hours, or when you delete them." />
        <Row title="Your history" detail="The list of your files, until you remove it." />
        <Row title="The audit log" detail="Time, action and result. Never file content. If you delete your account, it keeps no name or email." />
      </section>
      <Cookies />
      <section className="card">
        <div className="rowx">
          <div>
            <b>Delete my account</b>
            <div className="note">Removes your account, passkeys and files at once. Asks for your second step first.</div>
          </div>
          <button className="mbtn sm ghost danger" onClick={() => setAsking(true)}>
            Delete account
          </button>
        </div>
      </section>
      {asking && (
        <Dialog mood="alert" title="Delete your account?" sub="Your account, passkeys and files are removed at once. This cannot be undone." onClose={() => setAsking(false)}>
          {error && <Alert>{error}</Alert>}
          <div className="pair">
            <button className="mbtn danger" onClick={remove} disabled={busy}>
              Delete account
            </button>
            <button className="mbtn ghost" onClick={() => setAsking(false)}>
              Keep it
            </button>
          </div>
        </Dialog>
      )}
    </>
  )
}

export const Row = ({ title, detail, children }) => (
  <div className="lrow">
    <div>
      {title}
      <br />
      <span className="s">{detail}</span>
    </div>
    {children}
  </div>
)

export const Cookies = () => (
  <section className="card">
    <b>Cookies</b>
    <Row title="Keeps you signed in" detail="Ends after 30 minutes of nothing.">
      <Pill tone="ok">Needed</Pill>
    </Row>
    <Row title="Knows this device" detail="To warn you about a sign-in on a new one.">
      <Pill tone="ok">Needed</Pill>
    </Row>
    <Row title="Remembers light or dark" detail="Only your choice, nothing else.">
      <Pill tone="ok">Needed</Pill>
    </Row>
    <span className="note">No tracking. No ads. Nothing is shared.</span>
  </section>
)

function Notifications({ me, change, busy }) {
  const set = (settings) => change(() => api.changeSettings(settings))
  return (
    <>
      <section className="card">
        <b>In the app and by email</b>
        <Row title="My password, email or passkeys change" detail="Always on. It protects your account.">
          <Toggle label="Account changes, always on" on disabled />
        </Row>
        <Row title="Someone signs in on a new device" detail="Always on.">
          <Toggle label="New device, always on" on disabled />
        </Row>
      </section>
      <section className="card">
        <b>In the app only</b>
        <Row title="A file is ready or about to be deleted" detail="Shown on the bell.">
          <Toggle label="File notices" on={me.settings.fileNotices} disabled={busy} onChange={(fileNotices) => set({ fileNotices })} />
        </Row>
        <Row title="Sound when a job finishes" detail="One short sound.">
          <Toggle
            label="Sound when a job finishes"
            on={me.settings.finishSound}
            disabled={busy}
            onChange={(finishSound) => {
              if (finishSound) playDone()
              set({ finishSound })
            }}
          />
        </Row>
        <button className="link" onClick={playDone}>
          Play the sound
        </button>
      </section>
    </>
  )
}

function About() {
  const pages = [['files', 'How we handle your files'], ['privacy', 'Privacy notice'], ['cookies', 'Cookie notice'], ['terms', 'Terms of use'], ['contact', 'Contact']]
  return (
    <section className="card">
      <span className="m-sub">Doc2All checks, cleans and converts your documents. Nothing stays longer than 24 hours.</span>
      {pages.map(([to, label]) => (
        <Link key={to} className="lrow" to={`/${to}`}>
          <span>{label}</span>
          <span className="s" aria-hidden="true">
            ›
          </span>
        </Link>
      ))}
      <span className="note">Version 1.0</span>
    </section>
  )
}
