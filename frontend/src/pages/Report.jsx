// Screen 7: the safety report.
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { api } from '../api/calls.js'
import Cat from '../components/Cat.jsx'
import DeleteDialog from '../components/DeleteDialog.jsx'
import { Alert, Dialog, Pill, useAction } from '../components/ui.jsx'
import { dayAndTime, saveBlob } from '../lib/helpers.js'

const HEAD = {
  clear: { mood: 'safe', title: 'All clear', sub: 'checked, and nothing dangerous is left' },
  kept: { mood: 'hello', title: 'Done, one thing kept', sub: 'check before you share it' },
  alert: { mood: 'alert', title: 'Be careful', sub: 'I could not clean this file' },
  converted: { mood: 'hello', title: 'Converted', sub: 'not yet checked for hidden content' },
  failed: { mood: 'alert', title: 'It did not work', sub: 'I could not convert this file' },
}

export default function Report() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [dialog, setDialog] = useState(null) // 'delete' | 'why'
  const [busy, error, run] = useAction()

  useEffect(() => {
    setReport(null)
    run(async () => setReport(await api.report(jobId)))
  }, [jobId]) // eslint-disable-line react-hooks/exhaustive-deps

  if (error && !report) {
    return (
      <>
        <Alert>{error}</Alert>
        <Link className="link" to="/history">
          Back to my files
        </Link>
      </>
    )
  }
  if (!report) return <p className="note">Opening the report…</p>

  const head = HEAD[report.outcome]
  const nothingToDownload = report.outcome === 'alert' || report.outcome === 'failed'
  const download = () =>
    run(async () => {
      const { blob, name } = await api.download(report.resultId || report.fileId)
      saveBlob(blob, name)
    })
  const saveReport = () => {
    const lines = [`Doc2All safety report: ${report.fileName}`, head.title, '', ...report.findings.map((f) => `[${f.tag}] ${f.title}. ${f.detail}`)]
    saveBlob(new Blob([lines.join('\n')], { type: 'text/plain' }), `${report.fileName}.report.txt`)
  }

  return (
    <>
      <div className="rhead" data-mood={head.mood}>
        <Cat mood={head.mood} />
        <div>
          <h1 className="m-h">{head.title}</h1>
          <span className="m-sub">
            {report.fileName} · {head.sub}
          </span>
        </div>
      </div>
      <ul className="findings">
        {report.findings.map((f) => (
          <li key={f.title} className="find">
            <div className={f.ok ? 'ic ok' : 'ic warn'} aria-hidden="true">
              {f.ok ? '✓' : '!'}
            </div>
            <div>
              <b>{f.title}</b>
              <span>{f.detail}</span>
            </div>
            <Pill tone={!f.ok ? 'warn' : f.tag === 'Kept' ? 'info' : 'ok'}>{f.tag}</Pill>
          </li>
        ))}
      </ul>
      <div className="note center">{report.fileDeleted ? 'This file has been deleted. The report stays until you remove it from History.' : `⏱ Deleted automatically on ${dayAndTime(report.expiresAt)}`}</div>
      {error && <Alert>{error}</Alert>}
      <div className="actc">
        {!report.fileDeleted && nothingToDownload && (
          <button className="mbtn danger wide" onClick={() => setDialog('delete')}>
            Delete file
          </button>
        )}
        {!report.fileDeleted && !nothingToDownload && (
          <button className="mbtn wide" onClick={download} disabled={busy}>
            Download {{ clear: 'clean file', converted: 'PDF' }[report.outcome] || 'file'}
          </button>
        )}
        <div className="actr">
          {report.outcome === 'alert' && (
            <button className="mbtn sm ghost" onClick={() => setDialog('why')}>
              Why?
            </button>
          )}
          <button className="mbtn sm ghost" onClick={saveReport}>
            Save report
          </button>
          {!report.fileDeleted && !nothingToDownload && (
            <button className="mbtn sm ghost danger" onClick={() => setDialog('delete')}>
              Delete now
            </button>
          )}
          <Link className="mbtn sm ghost" to="/">
            Another file
          </Link>
        </div>
      </div>
      {dialog === 'delete' && <DeleteDialog file={{ id: report.fileId, name: report.fileName }} onClose={() => setDialog(null)} onDone={() => navigate('/history')} />}
      {dialog === 'why' && (
        <Dialog mood="alert" title="Why can I not clean it?" sub="Part of this file can still run a program, and I could not take it out safely." onClose={() => setDialog(null)}>
          <span className="m-sub">Do not open it and do not pass it on. Delete it, and ask the sender for a plain copy.</span>
          <button className="mbtn" onClick={() => setDialog(null)}>
            I understand
          </button>
        </Dialog>
      )}
    </>
  )
}
