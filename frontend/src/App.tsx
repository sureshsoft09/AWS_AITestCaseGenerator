import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom'
import './App.css'
import Dashboard from './components/Dashboard'
import Generate from './components/Generate'
import Enhance from './components/Enhance'

// Placeholder components - will be implemented in later tasks
const Migrate = () => <div className="placeholder-component">Migrate Component - Coming Soon</div>
const Analytics = () => <div className="placeholder-component">Analytics Component - Coming Soon</div>

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>MedAssureAI Platform</h1>
          <nav>
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/generate">Generate</Link>
            <Link to="/enhance">Enhance</Link>
            <Link to="/migrate">Migrate</Link>
            <Link to="/analytics">Analytics</Link>
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
