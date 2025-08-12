import React from "react"

export function Loader({ label = 'Loading...'}: { label?: string }) {
    return (
        <div style={{ padding: 24, fontFamily: 'system-ui, Arial' }}>
            <span aria-busy="true" aria-live="polite">{label}</span>
        </div>
    )
}
