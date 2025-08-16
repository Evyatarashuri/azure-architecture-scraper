import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import { Ask } from './pages/Ask'

function Home() {
  return (
    <div style={{ padding: 24 }}>
      <h2>Home</h2>
      <p>Backend health check is wired. Use the Ask page to query architectures.</p>
    </div>
  )
}

export default function App() {
  return (
    <div style={{ fontFamily: 'system-ui, Arial' }}>
      <nav style={{ display: 'flex', gap: 12, padding: 16, borderBottom: '1px solid #eee' }}>
        <Link to="/">Home</Link>
        <Link to="/ask">Ask</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/ask" element={<Ask />} />
      </Routes>
    </div>
  )
}
