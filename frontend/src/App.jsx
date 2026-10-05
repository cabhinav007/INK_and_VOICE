import React, { useState } from 'react'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import History from './pages/History'
import About from './pages/About'
import Blog from './pages/Blog'

function App() {
  const [currentPage, setCurrentPage] = useState('home')
  const [refreshHistoryTrigger, setRefreshHistoryTrigger] = useState(0)

  // Callback to force history page updates when a new audiobook is generated
  const triggerHistoryRefresh = () => {
    setRefreshHistoryTrigger(prev => prev + 1)
  }

  return (
    <div className="app-layout">
      {/* Floating Navbar */}
      <Navbar currentPage={currentPage} setCurrentPage={setCurrentPage} />
      
      {/* Dynamic Content Views */}
      <main className="content-view">
        <div style={{ display: currentPage === 'home' ? 'block' : 'none' }}>
          <Home onGenerationComplete={triggerHistoryRefresh} />
        </div>
        <div style={{ display: currentPage === 'history' ? 'block' : 'none' }}>
          <History refreshTrigger={refreshHistoryTrigger} active={currentPage === 'history'} />
        </div>
        <div style={{ display: currentPage === 'about' ? 'block' : 'none' }}>
          <About />
        </div>
        <div style={{ display: currentPage === 'blog' ? 'block' : 'none' }}>
          <Blog />
        </div>
      </main>
      
      {/* Small Artistic Footer */}
      <footer style={{
        textAlign: 'center', 
        padding: '40px 0 20px', 
        color: 'var(--text-muted)', 
        fontSize: '13px',
        fontFamily: 'var(--font-display)',
        letterSpacing: '0.05em'
      }}>
        © {new Date().getFullYear()} Ink & Voice, <br></br>Design and developed by PHANTOM .
      </footer>
    </div>
  )
}

export default App
