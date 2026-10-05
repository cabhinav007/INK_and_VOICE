import React from 'react'

function Navbar({ currentPage, setCurrentPage }) {
  return (
    <div className="navbar-wrapper">
      <nav className="navbar">
        {/* Animated Brand Logo */}
        <div className="logo-container" onClick={() => setCurrentPage('home')}>
          <div className="logo-wave">
            <span className="logo-wave-bar"></span>
            <span className="logo-wave-bar"></span>
            <span className="logo-wave-bar"></span>
            <span className="logo-wave-bar"></span>
          </div>
          <span className="text-neon-glow" style={{ fontWeight: 800 }}>Ink & Voice</span>
        </div>

        {/* Navigation Link Selection */}
        <ul className="nav-links">
          <li 
            className={`nav-link ${currentPage === 'home' ? 'active' : ''}`}
            onClick={() => setCurrentPage('home')}
          >
            Home
          </li>
          <li 
            className={`nav-link ${currentPage === 'history' ? 'active' : ''}`}
            onClick={() => setCurrentPage('history')}
          >
            Library
          </li>
          <li 
            className={`nav-link ${currentPage === 'about' ? 'active' : ''}`}
            onClick={() => setCurrentPage('about')}
          >
            About
          </li>
          <li 
            className={`nav-link ${currentPage === 'blog' ? 'active' : ''}`}
            onClick={() => setCurrentPage('blog')}
          >
            Blog
          </li>
        </ul>
      </nav>
    </div>
  )
}

export default Navbar
