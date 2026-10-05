import React from 'react'

function About() {
  return (
    <div className="container page-layout" style={{ animation: 'fadeIn 0.5s ease' }}>
      {/* Hero Header */}
      <section className="hero-wrapper" style={{ padding: '120px 0 40px' }}>
        <span className="hero-subtitle">The Acoustic Stage</span>
        <h1 className="hero-title text-gradient-display" style={{ fontSize: '42px', marginBottom: '16px' }}>
          Under the Hood of Ink & Voice
        </h1>
        <p className="hero-desc" style={{ fontSize: '15px', maxWidth: '600px', margin: '0 auto' }}>
          Unveiling the lightweight, local pipeline transforming written text into high-fidelity character-driven acoustic plays.
        </p>
      </section>

      {/* Visual Pipeline Flowchart */}
      <section className="card-row" style={{ marginBottom: '60px' }}>
        <div className="glass-panel" style={{ padding: '36px', textAlign: 'center' }}>
          <h2 style={{ fontSize: '24px', marginBottom: '28px', fontFamily: 'var(--font-display)' }}>The Auditory Stage Play</h2>
          
          {/* Timeline Grid */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '20px',
            flexWrap: 'wrap',
            marginTop: '20px'
          }}>
            {[
              { title: '1. Manuscript Analysis', desc: 'Parses PDF, Word, or text chapters into clean paragraphs.', icon: '✦' },
              { title: '2. Dialogue Attribution', desc: 'Statefully isolates narrative prose from character dialogues.', icon: '✧' },
              { title: '3. Vocal Casting', desc: 'Maps age, gender, and voice profiles to each character.', icon: '⚛' },
              { title: '4. Neural Synthesis', desc: 'Generates lifelike human speech locally using Kokoro-82M.', icon: '🎙️' },
              { title: '5. Acoustic Stitching', desc: 'Gaplessly merges vocal passages into a unified WAV audiobook.', icon: '⚖' }
            ].map((step, idx) => (
              <div key={idx} className="glass-panel" style={{
                flex: '1 1 180px',
                padding: '24px',
                background: 'rgba(255,255,255,0.01)',
                minHeight: '200px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                borderColor: 'rgba(255,255,255,0.03)'
              }}>
                <span style={{ fontSize: '28px', marginBottom: '16px', color: 'var(--accent)' }}>{step.icon}</span>
                <h4 style={{ fontSize: '14px', marginBottom: '8px', fontFamily: 'var(--font-display)', fontWeight: 600 }}>{step.title}</h4>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5' }}>{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Technology Breakdown */}
      <section style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
        gap: '30px',
        marginBottom: '60px'
      }}>
        {/* Card 1: Kokoro Model */}
        <div className="glass-panel" style={{ padding: '30px' }}>
          <h3 style={{ fontSize: '20px', marginBottom: '12px', color: 'var(--primary)', fontFamily: 'var(--font-display)' }}>🎙️ Neural Realism: Kokoro-82M</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', lineHeight: '1.6', marginBottom: '14px' }}>
            Traditional speech models require gigabytes of neural weights, placing a massive burden on memory and GPU storage. 
          </p>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', lineHeight: '1.6' }}>
            <strong>Ink & Voice</strong> solves this constraints-barrier by integrating <strong>Kokoro-82M</strong>. With just 82 million parameters, this model fits entirely in memory (under 82MB disk footprint), providing fluid human phrasing and prosody while remaining lightweight enough to render audiobooks locally on CPU or minimal GPU.
          </p>
        </div>

        {/* Card 2: Formant Pitch Shift Heuristics */}
        <div className="glass-panel" style={{ padding: '30px' }}>
          <h3 style={{ fontSize: '20px', marginBottom: '12px', color: 'var(--accent)', fontFamily: 'var(--font-display)' }}>🎛️ Acoustic Resonance & Formants</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', lineHeight: '1.6', marginBottom: '14px' }}>
            To create a broad spectrum of characters—from young children to mature elder speakers—without bloating the system, we employ native voice mapping combined with subtle formant pitch-shifting.
          </p>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', lineHeight: '1.6' }}>
            By adjusting speed rates in the synthesis graph and applying linear interpolation resampling, we gently shift acoustic frequencies to simulate different vocal tract shapes. This guarantees that young voices sound bright and senior voices sound deep and measured, without introducing speed artifacts or robotic distortion.
          </p>
        </div>
      </section>

      {/* Local execution section */}
      <section className="glass-panel" style={{ padding: '36px', textAlign: 'center' }}>
        <h3 style={{ fontSize: '20px', marginBottom: '12px', fontFamily: 'var(--font-display)' }}>🔒 Absolute Data Sovereignty</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '14px', maxWidth: '800px', margin: '0 auto 16px', lineHeight: '1.6' }}>
          Your novels and intellectual work deserve absolute protection. Ink & Voice is engineered to run 100% offline. Every line of text parsing and speech generation occurs locally in your system memory. No cloud dependencies, no API trackers—just pure, private local intelligence.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', flexWrap: 'wrap', marginTop: '20px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>💻 System: <strong>Windows (Fully Offline)</strong></span>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>⚙️ Memory Footprint: <strong>&lt; 150MB Overhead</strong></span>
        </div>
      </section>
    </div>
  )
}

export default About
