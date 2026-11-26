// Screen 8: my files. Pinned notices come from the frame around every page.
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api } from '../api/calls.js'
import DeleteDialog from '../components/DeleteDialog.jsx'
import { Alert, Corner, Pill, useAction } from '../components/ui.jsx'
import { saveBlob, timeLeft } from '../lib/helpers.js'

const RESULT = { clear: ['ok', 'All clear'], kept: ['info', 'Kept'], alert: ['warn', 'Problem'] }

export default function History() {
  const [items, setItems] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [busy, error, run] = useAction()
  const load = useCallback(async () => setItems((await api.history()).items), [])

  useEffect(() => {
    run(load)
  }, [load]) // eslint-disable-line react-hooks/exhaustive-deps

  const download = (item) =>
    run(async () => {
      const { blob, name } = await api.download(item.fileId)
      saveBlob(blob, name)
    })
  const remove = (item) =>
    run(async () => {
      await api.removeHistory(item.id)
      await load()
    })

  return (
    <>
      <div>
        <h1 className="m-h">Your files</h1>
        <span className="m-sub">Only you can see these.</span>
      </div>
      {error && <Alert>{error}</Alert>}
      {items?.length === 0 && (
        <div className="drop">
          <strong>No files yet</strong>
          <Link className="mbtn sm" to="/">
            Add a file
          </Link>
        </div>
      )}
      {items?.length > 0 && (
        <div className="scroll-x">
          <table className="tbl">
            <thead>
              <tr>
                <th>File</th>
                <th className="hide-s">Did</th>
                <th>Result</th>
                <th className="hide-s">Deletes in</th>
                <th>
                  <span className="sr">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <b>{item.name}</b>
                  </td>
                  <td className="hide-s">{item.did}</td>
                  <td>{item.deleted ? <Pill tone="mute">File deleted</Pill> : <Pill tone={RESULT[item.outcome][0]}>{RESULT[item.outcome][1]}</Pill>}</td>
                  <td className="hide-s">{item.deleted ? 'Gone' : timeLeft(item.expiresAt)}</td>
                  <td>
                    <div className="acts">
                      <Link to={`/report/${item.jobId}`}>Report</Link>
                      {!item.deleted && item.outcome !== 'alert' && (
                        <button onClick={() => download(item)} disabled={busy}>
                          Download
                        </button>
                      )}
                      {item.deleted ? (
                        <button className="del" onClick={() => remove(item)} disabled={busy}>
                          Remove
                        </button>
                      ) : (
                        <button className="del" onClick={() => setDeleting(item)}>
                          Delete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {deleting && (
        <DeleteDialog
          file={{ id: deleting.fileId, name: deleting.name }}
          onClose={() => setDeleting(null)}
          onDone={() => {
            setDeleting(null)
            run(load)
          }}
        />
      )}
      <Corner>Nothing stays longer than 24 hours.</Corner>
    </>
  )
}
