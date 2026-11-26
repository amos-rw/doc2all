// Screens 5 and 6: upload, choose, check what is hidden, black out, consent for outside OCR, and wait.
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import { api } from '../api/calls.js'
import { isDemo } from '../api/client.js'
import { useRefreshNotices } from '../components/Layout.jsx'
import { Alert, Corner, Dialog, Icon, Pill, Steps, useAction } from '../components/ui.jsx'
import { playDone, size } from '../lib/helpers.js'

const STEPS = ['Upload', 'Choose', 'Wait', 'Download']
const TOOLS = [
  { key: 'convert', name: 'Convert', does: (kind) => (kind === 'pdf' ? 'PDF to images' : 'Word or PowerPoint to PDF') },
  { key: 'clean', name: 'Clean', does: () => 'Remove hidden data' },
  { key: 'scan', name: 'Scan to text', does: () => 'Read a photo or scan' },
  { key: 'blackout', name: 'Black out', does: () => 'Hide personal data' },
]
const SAMPLES = [
  { name: 'contract.docx', start: [0x50, 0x4b, 3, 4], note: 'a normal file' },
  { name: 'scan-id.jpg', start: [0xff, 0xd8, 0xff], note: 'a scan' },
  { name: 'invoice.docx', start: [0x50, 0x4b, 3, 4], note: 'cannot be cleaned' },
  { name: 'report.pdf', start: [0x4d, 0x5a], note: 'really a program' },
]
const MATCH_NAMES = { ids: 'ID numbers', phones: 'Phone numbers', emails: 'Emails' }

const sample = ({ name, start }) => new File([new Uint8Array([...start, ...new Array(2000).fill(0)])], name)

export default function Tools() {
  const navigate = useNavigate()
  const refreshNotices = useRefreshNotices()
  const [view, setView] = useState('pick')
  const [file, setFile] = useState(null)
  const [actions, setActions] = useState([])
  const [refusal, setRefusal] = useState('')
  const [groups, setGroups] = useState([])
  const [preview, setPreview] = useState(null)
  const [hidden, setHidden] = useState([]) // matches to black out
  const [job, setJob] = useState(null)
  const [busy, error, run] = useAction()
  const choices = useRef({})
  const alive = useRef(true)

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])

  const startOver = () => {
    setFile(null)
    setActions([])
    setView('pick')
    choices.current = {}
  }

  const upload = (chosen) => {
    if (!chosen) return
    run(async () => {
      try {
        const saved = await api.upload(chosen)
        setFile(saved)
        setActions(saved.allowed.includes('convert') ? ['convert', 'clean'] : ['scan'])
        setView('pick')
        choices.current = {}
      } catch (problem) {
        if (problem.code !== 'refused') throw problem
        setRefusal(problem.message)
        setView('rejected')
      }
    })
  }

  // Ask the questions the chosen tools need, one after another, then start the job.
  const next = async () => {
    const made = choices.current
    if (actions.includes('clean') && !made.keep) {
      setGroups((await api.check(file.id)).groups)
      return setView('clean')
    }
    if (actions.includes('blackout') && !made.blackout) {
      const found = await api.matches(file.id)
      setPreview(found)
      setHidden(found.matches.map((m) => m.id))
      return setView('blackout')
    }
    if (actions.includes('scan') && made.outsideOcr === undefined) return setView('consent')

    const { id } = await api.startJob({ fileId: file.id, actions, ...made })
    setView('checking')
    let state = await api.job(id)
    while (alive.current && state.status === 'working') {
      setJob(state)
      await new Promise((resolve) => setTimeout(resolve, 500))
      state = await api.job(id)
    }
    if (!alive.current) return undefined
    const me = await api.me()
    if (me.settings.finishSound) playDone()
    refreshNotices()
    navigate(`/report/${id}`)
    return undefined
  }
  const answer = (choice) => {
    Object.assign(choices.current, choice)
    run(next)
  }
  const toggleAction = (key) => {
    setActions(actions.includes(key) ? actions.filter((a) => a !== key) : [...actions, key])
    choices.current = {}
  }

  const chip = file && (
    <div className="chipf">
      {file.name} <Pill tone="mute">{size(file.size)}</Pill>
    </div>
  )

  if (view === 'rejected') {
    return (
      <>
        <Steps labels={STEPS} active={1} />
        <div className="drop bad" role="alert">
          <strong className="refused">I did not open this file.</strong>
          <span className="strong">{refusal}</span>
          <span className="note">Nothing was saved. Nobody else saw it.</span>
          <button className="mbtn sm ghost" onClick={startOver}>
            Choose another file
          </button>
        </div>
        <Corner mood="alert">Careful!</Corner>
      </>
    )
  }

  if (view === 'clean') {
    return (
      <>
        <Steps labels={STEPS} active={2} />
        {chip}
        <CleanOptions groups={groups} onChange={setGroups} />
        {error && <Alert>{error}</Alert>}
        <div className="actr">
          <button className="mbtn" disabled={busy} onClick={() => answer({ keep: groups.filter((g) => !g.remove).map((g) => g.key) })}>
            Clean it
          </button>
          <button className="mbtn ghost" onClick={startOver}>
            Cancel
          </button>
        </div>
        <Corner>Dangerous things always go. The rest is yours.</Corner>
      </>
    )
  }

  if (view === 'blackout') {
    const flip = (ids, on) => setHidden(on ? [...new Set([...hidden, ...ids])] : hidden.filter((id) => !ids.includes(id)))
    return (
      <>
        <Steps labels={STEPS} active={2} />
        <div className="bo">
          <div className="paper-m">
            <b>{preview.title}</b>
            <br />
            {preview.person}
            {preview.matches.map((m) => (
              <div key={m.id}>
                {m.label}:{' '}
                <button className={hidden.includes(m.id) ? 'hl' : 'hl off'} aria-pressed={hidden.includes(m.id)} onClick={() => flip([m.id], !hidden.includes(m.id))}>
                  {m.value}
                </button>
              </div>
            ))}
          </div>
          <div className="card">
            <b>I found {preview.matches.length} things</b>
            {Object.entries(MATCH_NAMES).map(([kind, label]) => {
              const ids = preview.matches.filter((m) => m.kind === kind).map((m) => m.id)
              const chosen = ids.filter((id) => hidden.includes(id)).length
              return (
                <label key={kind} className="lrow">
                  <span className="choice">
                    <input type="checkbox" checked={chosen === ids.length} onChange={(e) => flip(ids, e.target.checked)} />
                    <span>
                      {label}
                      <br />
                      <span className="s">
                        {chosen} of {ids.length} will be blacked out
                      </span>
                    </span>
                  </span>
                </label>
              )
            })}
            <span className="note">Looks wrong? Press a match to keep it.</span>
            {error && <Alert>{error}</Alert>}
            <button className="mbtn" disabled={busy} onClick={() => answer({ blackout: hidden })}>
              Black out
            </button>
            <button className="link center" onClick={startOver}>
              Cancel
            </button>
          </div>
        </div>
        <Corner mood="checking">Check the yellow parts.</Corner>
      </>
    )
  }

  if (view === 'checking') {
    return (
      <>
        <Steps labels={STEPS} active={3} />
        {chip}
        {error && <Alert>{error}</Alert>}
        <ul className="prog" aria-live="polite">
          {(job?.steps || []).map((step, i) => (
            <li key={step.label} className={{ done: 'd', now: 'n', waiting: 'w' }[step.state]}>
              <b>{step.state === 'done' ? '✓' : step.state === 'now' ? '…' : i + 1}</b>
              {step.label}
            </li>
          ))}
        </ul>
        <div className="bar" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round((job?.progress || 0) * 100)}>
          <i style={{ width: `${(job?.progress || 0) * 100}%` }} />
        </div>
        <span className="note">Usually under 30 seconds. A short sound tells you when it is done.</span>
        <Corner mood="checking">Looking closely…</Corner>
      </>
    )
  }

  return (
    <>
      <Steps labels={STEPS} active={file ? 2 : 1} />
      <label
        className="drop"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          upload(e.dataTransfer.files[0])
        }}
      >
        <span className="drop-icon">{Icon.up}</span>
        <strong>{busy && !file ? 'Checking the file…' : file ? file.name : 'Drop a file here, or press to choose'}</strong>
        <span className="note">PDF, Word, PowerPoint, PNG or JPG · up to 20 MB</span>
        <input
          type="file"
          accept=".pdf,.docx,.pptx,.png,.jpg,.jpeg"
          onChange={(e) => {
            upload(e.target.files[0])
            e.target.value = ''
          }}
        />
      </label>
      {isDemo && !file && (
        <div className="demohint">
          Demo files:{' '}
          {SAMPLES.map((s) => (
            <button key={s.name} className="link small" disabled={busy} onClick={() => upload(sample(s))}>
              {s.name} ({s.note})
            </button>
          ))}
        </div>
      )}
      <div className="tools" role="group" aria-label="What to do with the file">
        {TOOLS.map((tool) => {
          const possible = !file || file.allowed.includes(tool.key)
          const on = actions.includes(tool.key)
          return (
            <button key={tool.key} className={on ? 'tool on' : 'tool'} aria-pressed={on} disabled={!file || !possible} onClick={() => toggleAction(tool.key)}>
              {tool.name}
              <span>{possible ? tool.does(file?.kind) : 'Not for this kind of file'}</span>
            </button>
          )
        })}
      </div>
      {error && <Alert>{error}</Alert>}
      {file && (
        <div className="actr">
          <button className="mbtn" disabled={busy || !actions.length} onClick={() => run(next)}>
            Check and start
          </button>
          <button className="mbtn ghost" onClick={startOver}>
            Cancel
          </button>
        </div>
      )}
      {view === 'consent' && <Consent fileName={file.name} busy={busy} onAnswer={(outsideOcr) => answer({ outsideOcr })} onClose={() => setView('pick')} />}
      <Corner>{file ? 'Now choose what I should do.' : 'Drop a file in. I look at it first.'}</Corner>
    </>
  )
}

function CleanOptions({ groups, onChange }) {
  const set = (key, remove) => onChange(groups.map((g) => (g.key === key ? { ...g, remove } : g)))
  return (
    <>
      <div>
        <h1 className="m-h">I found this in your file</h1>
        <span className="m-sub">Switch off only what you need to keep. Code written as text on a page is never changed.</span>
      </div>
      <div className="card">
        {groups.map((g) => (
          <label key={g.key} className="lrow">
            <span className="choice">
              <input type="checkbox" checked={g.rule === 'always' || g.remove} disabled={g.rule === 'always'} onChange={(e) => set(g.key, e.target.checked)} />
              <span>
                {g.title}
                <br />
                <span className="s">{g.detail}</span>
              </span>
            </span>
            {g.rule === 'always' && <Pill tone="mute">Always removed</Pill>}
            {g.rule !== 'always' && !g.remove && <Pill tone="info">Keep</Pill>}
          </label>
        ))}
      </div>
    </>
  )
}

function Consent({ fileName, busy, onAnswer, onClose }) {
  const [outside, setOutside] = useState(false)
  return (
    <Dialog mood="checking" title="Where should I read this scan?" sub={fileName} onClose={onClose}>
      <label className={outside ? 'opt' : 'opt on'}>
        <input type="radio" name="where" checked={!outside} onChange={() => setOutside(false)} />
        <span>
          <b>
            On our server <Pill tone="ok">Recommended</Pill>
          </b>
          <span>Your file never leaves. This is the default.</span>
        </span>
      </label>
      <label className={outside ? 'opt on' : 'opt'}>
        <input type="radio" name="where" checked={outside} onChange={() => setOutside(true)} />
        <span>
          <b>With an outside service</b>
          <span>Better for messy scans. Your text leaves our server, for this file only.</span>
        </span>
      </label>
      <div className="pair">
        <button className="mbtn" disabled={busy} onClick={() => onAnswer(false)}>
          Keep it private
        </button>
        <button className="mbtn ghost" disabled={busy || !outside} onClick={() => onAnswer(true)}>
          Allow for this file
        </button>
      </div>
    </Dialog>
  )
}
