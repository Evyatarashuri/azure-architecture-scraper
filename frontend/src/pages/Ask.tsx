import React from 'react'
import { askQuestion, type AskResponse } from '@/api/rag'

export function Ask() {
  const [q, setQ] = React.useState('')
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string>('')
  const [answer, setAnswer] = React.useState<string>('')
  const [raw, setRaw] = React.useState<AskResponse | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const question = q.trim()
    if (!question) return
    setLoading(true); setError(''); setAnswer(''); setRaw(null)
    try {
      const data = await askQuestion(question)
      setAnswer((data as any)?.answer ?? '')
      setRaw(data)
    } catch (err: any) {
      setError(err?.message ?? 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 880, margin: '0 auto', fontFamily: 'system-ui, Arial' }}>
      <h1>Ask the Architecture Assistant</h1>
      <form onSubmit={onSubmit} style={{ marginTop: 16, display: 'grid', gap: 8 }}>
        <label htmlFor="q">Your question</label>
        <textarea
          id="q"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          rows={4}
          placeholder="Type an Azure architecture question…"
          style={{ padding: 12, fontSize: 16 }}
          required
        />
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="submit" disabled={loading || q.trim().length === 0} style={{ padding: '8px 14px' }}>
            {loading ? 'Asking…' : 'Ask'}
          </button>
          <button type="button" onClick={() => { setAnswer(''); setRaw(null); setError(''); setQ('') }}>
            Clear
          </button>
        </div>
      </form>

      {error && <p style={{ color: 'crimson', marginTop: 12 }}>Error: {error}</p>}

      {answer && (
        <section style={{ marginTop: 20 }}>
          <h2>Answer</h2>
          <div style={{ background: '#fafafa', padding: 12, border: '1px solid #eee' }}>
            <pre style={{ whiteSpace: 'pre-wrap' }}>{answer}</pre>
          </div>
        </section>
      )}

      {raw && raw.sources?.length ? (
        <section style={{ marginTop: 16 }}>
          <h3>Sources</h3>
          <ul>
            {raw.sources.map((s, i) => (
              <li key={i}><a href={s.url} target="_blank" rel="noreferrer">{s.title || s.url}</a></li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  )
}
