// "Delete this file now?" and then "Gone!" (design screen 9).
import { useState } from 'react'
import { api } from '../api/calls.js'
import { clock } from '../lib/helpers.js'
import { Alert, Dialog, useAction } from './ui.jsx'

export default function DeleteDialog({ file, onClose, onDone }) {
  const [deletedAt, setDeletedAt] = useState(null)
  const [busy, error, run] = useAction()
  const remove = () => run(async () => setDeletedAt((await api.deleteFile(file.id)).deletedAt))

  if (deletedAt) {
    return (
      <Dialog key="done" mood="safe" title="Gone!" sub={`${file.name} was deleted.`} onClose={onDone}>
        <Alert tone="good">Written to the log at {clock(deletedAt)}. No file content was kept.</Alert>
        <button className="mbtn" onClick={onDone}>
          Back to my files
        </button>
      </Dialog>
    )
  }
  return (
    <Dialog key="ask" mood="alert" title="Delete this file now?" onClose={onClose}>
      <div className="chipf">{file.name}</div>
      <span className="m-sub">I remove the file and its results. A line in the log keeps the time, not the content.</span>
      {error && <Alert>{error}</Alert>}
      <div className="pair">
        <button className="mbtn danger" onClick={remove} disabled={busy}>
          Delete now
        </button>
        <button className="mbtn ghost" onClick={onClose}>
          Keep it
        </button>
      </div>
    </Dialog>
  )
}
