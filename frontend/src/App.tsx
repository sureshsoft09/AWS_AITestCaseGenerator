import { BrowserRouter as Router, Routes, Route, Navigate, NavLink } from 'react-router-dom'
import './App.css'
import Dashboard from './components/Dashboard'
import Generate from './components/Generate'
import Enhance from './components/Enhance'

// Placeholder components - will be implemented in later tasks
const Migrate = () => (
  <div className="placeholder-component">
    <div style={{ textAlign: 'center' }}>
      <h2 style={{ marginBottom: '1rem', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>🚀 Migrate Component</h2>
      <p style={{ color: '#718096' }}>Coming Soon</p>
    </div>
  </div>
)

const Analytics = () => (
  <div className="placeholder-component">
    <div style={{ textAlign: 'center' }}>
      <h2 style={{ marginBottom: '1rem', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>📊 Analytics Component</h2>
      <p style={{ color: '#718096' }}>Coming Soon</p>
    </div>
  </div>
)

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>🏥 MedAssureAI Platform</h1>
          <nav>
            <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'active' : ''}>📊 Dashboard</NavLink>
            <NavLink to="/generate" className={({ isActive }) => isActive ? 'active' : ''}>✨ Generate</NavLink>
            <NavLink to="/enhance" className={({ isActive }) => isActive ? 'active' : ''}>🔧 Enhance</NavLink>
            <NavLink to="/migrate" className={({ isActive }) => isActive ? 'active' : ''}>🚀 Migrate</NavLink>
            <NavLink to="/analytics" className={({ isActive }) => isActive ? 'active' : ''}>📈 Analytics</NavLink>
          </nav>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/generate" element={<Generate />} />
            <Route path="/enhance" element={<Enhance />} />
            <Route path="/migrate" element={<Migrate />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
