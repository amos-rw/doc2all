// The small pieces every page is made of.
import { useEffect, useId, useRef, useState } from 'react'
import { Link } from 'react-router'
import { isDemo } from '../api/client.js'
import Cat from './Cat.jsx'

const svg = (size, width, children) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={width} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {children}
  </svg>
)

export const Icon = {
  key: svg(24, 2.4, <><circle cx="8" cy="15" r="4.5" /><path d="M11.5 11.5L20 3M16 7l3 3" /></>),
  up: svg(40, 2.2, <path d="M12 16V4M7 9l5-5 5 5M4 20h16" />),
  bell: svg(20, 2.2, <><path d="M6 9a6 6 0 0 1 12 0c0 6 2.5 7.5 2.5 7.5h-17S6 15 6 9z" /><path d="M10 20a2 2 0 0 0 4 0" /></>),
  tools: svg(20, 2.2, <><rect x="4" y="4" width="7" height="7" rx="2" /><rect x="13" y="4" width="7" height="7" rx="2" /><rect x="4" y="13" width="7" height="7" rx="2" /><rect x="13" y="13" width="7" height="7" rx="2" /></>),
  clock: svg(20, 2.2, <><circle cx="12" cy="12" r="8.5" /><path d="M12 7v5l3 2" /></>),
  user: svg(20, 2.2, <><circle cx="12" cy="8.5" r="3.6" /><path d="M5 20c.8-3.6 3.6-5.2 7-5.2s6.2 1.6 7 5.2" /></>),
  log: svg(20, 2.2, <><path d="M6 4h9l3 3v13H6z" /><path d="M9 11h6M9 15h6" /></>),
}

// Runs a call, keeps "busy" while it works and the plain error message when it is refused.
export function useAction() {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const run = async (action) => {
    setError(null)
    setBusy(true)
    try {
      return await action()
    } catch (problem) {
      if (problem.code !== 'cancelled') setError(problem.message)
      return undefined
    } finally {
      setBusy(false)
    }
  }
  return [busy, error, run, setError]
}

export function Field({ label, type = 'text', value, onChange, ...rest }) {
  const id = useId()
  const [shown, setShown] = useState(false)
  const secret = type === 'password'
  return (
    <div className="fld">
      <label htmlFor={id}>{label}</label>
      <div className="inp">
        <input id={id} type={secret && shown ? 'text' : type} value={value} onChange={(e) => onChange(e.target.value)} {...rest} />
        {secret && (
          <button type="button" className="link small" onClick={() => setShown(!shown)}>
            {shown ? 'Hide' : 'Show'}
          </button>
        )}
      </div>
    </div>
  )
}

// Six boxes, one real input on top of them so typing, pasting and screen readers work as usual.
export function CodeInput({ value, onChange }) {
  return (
    <div className="codebox">
      <div className="codes" aria-hidden="true">
        {Array.from({ length: 6 }, (_, i) => (
          <i key={i} className={i === value.length ? 'on' : ''}>
            {value[i] || ''}
          </i>
        ))}
      </div>
      <input aria-label="6 digit code" inputMode="numeric" autoComplete="one-time-code" maxLength={6} autoFocus value={value} onChange={(e) => onChange(e.target.value.replace(/\D/g, '').slice(0, 6))} />
    </div>
  )
}

export function Strength({ password }) {
  if (!password) return <div className="strength">Use 12 or more characters.</div>
  const kinds = [/[a-z]/, /[A-Z]/, /\d/, /[^\w]/].filter((k) => k.test(password)).length
  const level = password.length < 12 ? 'weak' : password.length >= 16 || kinds >= 3 ? 'strong' : 'medium'
  const missing = 12 - password.length
  return (
    <div className="strength" aria-live="polite">
      <span>Password strength:</span>
      <b className={level}>{level[0].toUpperCase() + level.slice(1)}</b>
      {missing > 0 && <span className="hint">Use 12 or more characters. {missing} more to go.</span>}
    </div>
  )
}

export function Steps({ labels, active }) {
  return (
    <ol className="steps" aria-label="Progress">
      {labels.map((label, i) => (
        <li key={label} className={i + 1 < active ? 'done' : i + 1 === active ? 'on' : ''} aria-current={i + 1 === active ? 'step' : undefined}>
          <b>{i + 1 < active ? '✓' : i + 1}</b>
          {label}
        </li>
      ))}
    </ol>
  )
}

export const Pill = ({ tone, children }) => <span className={`pill ${tone}`}>{children}</span>

export const Alert = ({ tone = 'bad', children }) => (
  <div className={`alertbox ${tone}`} role="alert">
    {tone === 'bad' ? '✕' : '✓'} {children}
  </div>
)

export const DemoHint = ({ children }) => (isDemo ? <div className="demohint">Demo: {children}</div> : null)

export function Dialog({ title, sub, mood = 'hello', onClose, children }) {
  const ref = useRef(null)
  const id = useId()
  useEffect(() => {
    const dialog = ref.current
    if (!dialog.open) dialog.showModal()
    return () => dialog.close()
  }, [])
  return (
    <dialog
      ref={ref}
      className="dialog"
      aria-labelledby={id}
      onCancel={(event) => {
        event.preventDefault()
        onClose?.()
      }}
    >
      <div className="dcat">
        <Cat mood={mood} />
        <div>
          <h2 id={id} className="m-h dialog-h">
            {title}
          </h2>
          {sub && <span className="m-sub">{sub}</span>}
        </div>
      </div>
      {children}
    </dialog>
  )
}

export const Corner = ({ mood = 'hello', children }) => (
  <div className="corner">
    <div className="bubble">{children}</div>
    <Cat mood={mood} />
  </div>
)

export const LegalLinks = () => (
  <nav className="legal" aria-label="About Doc2All">
    <Link to="/privacy">Privacy</Link>
    <Link to="/cookies">Cookies</Link>
    <Link to="/about">About</Link>
  </nav>
)

// The pages before sign-in: the cat on one side, the form on the other.
export function AuthLayout({ mood = 'hello', say, children }) {
  return (
    <main className="m-auth">
      <div className="m-catp" data-mood={mood}>
        <Link to="/sign-in" className="m-brand">
          Doc<b>2</b>All
        </Link>
        <Cat mood={mood} />
        <div className="bubble" aria-live="polite">
          {say}
        </div>
      </div>
      <div className="m-form">
        <div className="m-form-in">
          {children}
          <LegalLinks />
        </div>
      </div>
    </main>
  )
}

export function Toggle({ on, onChange, label, disabled }) {
  return <button type="button" role="switch" aria-checked={on} aria-label={label} className={on ? 'toggle' : 'toggle off'} disabled={disabled} onClick={() => onChange?.(!on)} />
}
