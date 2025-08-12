import React from "react";
import { api } from "../api/client";

export function Home() {
    const [ping, setPing] = React.useState<string>("");
    const [error, setError] = React.useState<string>("");

    React.useEffect(() => {
        api.get("/health")
            .then(res => setPing(res.data?.status ?? 'OK'))
            .catch(err => setError(err?.message ?? 'Request failed'))
    }, [])

  return (
    <div style={{ padding: 24, fontFamily: 'system-ui, Arial' }}>
      <h1>FastAPI × React (TypeScript)</h1>
      <p>Build time: {String((globalThis as any).__APP_BUILD_TIME__)}</p>

      <section style={{ marginTop: 16 }}>
        <h2>Backend Health</h2>
        {!error ? (
          <p>Backend says: <strong>{ping || '...'}</strong></p>
        ) : (
          <p style={{ color: 'crimson' }}>Error: {error}</p>
        )}
      </section>
    </div>
  )
}
