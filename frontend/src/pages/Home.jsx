import React, { useState, useEffect, useRef } from 'react'

// Kokoro voices — used ONLY for the Narrator
const NARRATOR_VOICES = [
  { id: 'af_nicole', name: 'Nicole (Clear & Narrative)' },
  { id: 'af_sarah', name: 'Sarah (Warm & Emotional)' },
  { id: 'af_bella', name: 'Bella (Soft & Gentle)' },
  { id: 'af_sky', name: 'Sky (Crisp & Energetic)' },
  { id: 'am_adam', name: 'Adam (Deep & Authoritative)' },
  { id: 'am_michael', name: 'Michael (Smooth & Conversational)' },
]

// Neural voices — used for character dialogues (grouped by gender and age)
const CHARACTER_VOICES = {
  Female: {
    Young: [
      { id: 'bf_emma', name: 'Emma (Young, UK)' },
      { id: 'bf_isabella', name: 'Isabella (Young, UK)' },
      { id: 'af_bella', name: 'Bella (Soft, US)' },
    ],
    'Mid-Age': [
      { id: 'af_nicole', name: 'Nicole (Clear, US)' },
      { id: 'af_sarah', name: 'Sarah (Warm, US)' },
      { id: 'af_sky', name: 'Sky (Crisp, US)' },
      { id: 'af_heart', name: 'Heart (Expressive, US)' },
      { id: 'af_alloy', name: 'Alloy (Neutral, US)' },
      { id: 'af_jessica', name: 'Jessica (Bright, US)' },
      { id: 'af_kore', name: 'Kore (Gentle, US)' },
      { id: 'af_nova', name: 'Nova (Energetic, US)' },
      { id: 'af_river', name: 'River (Smooth, US)' },
    ],
    Senior: [
      { id: 'af_sarah', name: 'Margaret (Mature, US)' },
      { id: 'bf_isabella', name: 'Dorothy (Seasoned, UK)' },
    ],
  },
  Male: {
    Young: [
      { id: 'am_puck', name: 'Puck (Young, US)' },
      { id: 'bm_lewis', name: 'Lewis (Young, UK)' },
    ],
    'Mid-Age': [
      { id: 'am_adam', name: 'Adam (Deep, US)' },
      { id: 'am_michael', name: 'Michael (Smooth, US)' },
      { id: 'bm_george', name: 'George (Polished, UK)' },
      { id: 'bm_daniel', name: 'Daniel (Conversational, UK)' },
      { id: 'am_fenrir', name: 'Fenrir (Strong, US)' },
      { id: 'bm_fable', name: 'Fable (Measured, UK)' },
    ],
    Senior: [
      { id: 'am_adam', name: 'Arthur (Mature, US)' },
      { id: 'bm_george', name: 'Edward (Seasoned, UK)' },
    ],
  },
}

// Helper: get voice options for a character based on gender + age
function getCharacterVoices(gender, ageGroup) {
  const genderVoices = CHARACTER_VOICES[gender]
  if (!genderVoices) return CHARACTER_VOICES.Female['Mid-Age']
  return genderVoices[ageGroup] || genderVoices['Mid-Age']
}

// Helper: pick default voice for gender + age
function getDefaultCharacterVoice(gender, ageGroup) {
  const options = getCharacterVoices(gender, ageGroup)
  return options[0]?.id || 'af_nicole'
}

function Home({ onGenerationComplete }) {
  // Upload and Parsing state
  const [file, setFile] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisStep, setAnalysisStep] = useState(0)
  const [sessionId, setSessionId] = useState(null)
  const [title, setTitle] = useState('')
  const [characters, setCharacters] = useState([])
  const [allChunks, setAllChunks] = useState([])
  const [totalChunks, setTotalChunks] = useState(0)
  
  // Custom voices configuration state
  const [voicesConfig, setVoicesConfig] = useState({})

  // Generation status state
  const [generationStatus, setGenerationStatus] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)

  // Audio queue playing states
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentChunkIdx, setCurrentChunkIdx] = useState(0)
  const [playbackTime, setPlaybackTime] = useState(0)
  const [playbackDuration, setPlaybackDuration] = useState(0)
  const [isBuffering, setIsBuffering] = useState(false)
  const [volume, setVolume] = useState(0.85)
  
  const audioRef = useRef(new Audio())
  const previewAudioRef = useRef(null)
  const pollIntervalRef = useRef(null)
  const productionSectionRef = useRef(null)

  // Clean up timers on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.src = ""
      }
      if (previewAudioRef.current) {
        previewAudioRef.current.pause()
        previewAudioRef.current.src = ""
      }
    }
  }, [])

  // Drag and Drop handlers
  const handleDragOver = (e) => { e.preventDefault() }

  const handleDrop = (e) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadAndAnalyze(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      uploadAndAnalyze(e.target.files[0])
    }
  }

  // API Call: Upload & analyze document
  const uploadAndAnalyze = async (uploadedFile) => {
    setFile(uploadedFile)
    setIsAnalyzing(true)
    setAnalysisStep(0)
    setSessionId(null)
    setCharacters([])
    setAllChunks([])
    
    let currentStep = 0
    const stepInterval = setInterval(() => {
      if (currentStep < 3) { currentStep++; setAnalysisStep(currentStep) }
      else clearInterval(stepInterval)
    }, 1200)

    const formData = new FormData()
    formData.append('file', uploadedFile)

    try {
      const response = await fetch('/api/upload', { method: 'POST', body: formData })
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Failed to upload novel.')
      }

      const data = await response.json()
      clearInterval(stepInterval)
      setSessionId(data.session_id)
      setTitle(data.title)
      setCharacters(data.characters)
      setTotalChunks(data.total_chunks)
      setAllChunks(data.chunks)
      
      // Initialize voice configs — Narrator and characters mapped to default profiles
      const initialConfig = {}
      data.characters.forEach(char => {
        const isNarrator = char.name === 'Narrator'
        initialConfig[char.name] = {
          voice: char.voice || (isNarrator ? 'af_nicole' : getDefaultCharacterVoice(char.gender, char.ageGroup)),
          gender: char.gender,
          ageGroup: char.ageGroup,
        }
      })
      setVoicesConfig(initialConfig)
      setIsAnalyzing(false)
    } catch (e) {
      clearInterval(stepInterval)
      setIsAnalyzing(false)
      setFile(null)
      alert(e.message)
    }
  }

  // Handle voice property adjustments
  const handleCharVoiceChange = (charName, key, value) => {
    setVoicesConfig(prev => {
      const isNarrator = charName === 'Narrator'
      const updated = { ...prev[charName], [key]: value }
      
      // When gender or age changes, auto-assign a suitable default voice
      if ((key === 'gender' || key === 'ageGroup') && !isNarrator) {
        const g = key === 'gender' ? value : updated.gender
        const a = key === 'ageGroup' ? value : updated.ageGroup
        updated.voice = getDefaultCharacterVoice(g, a)
      }
      
      return { ...prev, [charName]: updated }
    })
  }

  // Real voice preview fetched directly from the backend Kokoro engine
  const playVoicePreview = (charName) => {
    const config = voicesConfig[charName]
    if (!config) return
    window.speechSynthesis.cancel() // cancel browser speech synthesis fallback
    
    // Stop any currently playing preview
    if (previewAudioRef.current) {
      try {
        previewAudioRef.current.pause()
        previewAudioRef.current.src = ""
      } catch (e) {}
      previewAudioRef.current = null
    }
    
    const audioUrl = `/api/preview?voice=${config.voice}&gender=${config.gender}&ageGroup=${config.ageGroup}`
    const previewAudio = new Audio(audioUrl)
    previewAudio.volume = volume
    previewAudioRef.current = previewAudio
    previewAudio.play().catch(e => console.error("Preview playback failed:", e))
  }

  // API Call: Start generation
  const startAudiobookGeneration = async () => {
    if (!sessionId) return
    setIsGenerating(true)
    setCurrentChunkIdx(0)
    setIsPlaying(false)
    setPlaybackTime(0)
    setPlaybackDuration(0)
    
    // Set pending status immediately to show stage production columns instantly
    setGenerationStatus({
      session_id: sessionId,
      title: title,
      status: "pending",
      progress: 0,
      completed_chunks: [],
      total_chunks: totalChunks,
      audiobook_id: null,
      generation_time: null
    })

    // Scroll viewport down to acoustic stage production immediately
    setTimeout(() => {
      productionSectionRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, 100)

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, title, voices: voicesConfig })
      })
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Failed to start voice generation.')
      }
      pollIntervalRef.current = setInterval(pollGenerationStatus, 1000)
    } catch (e) {
      setIsGenerating(false)
      alert(e.message)
    }
  }

  // Poll generation status
  const pollGenerationStatus = async () => {
    if (!sessionId) return
    try {
      const response = await fetch(`/api/status/${sessionId}`)
      if (!response.ok) return
      const status = await response.json()
      setGenerationStatus(status)

      if (status.completed_chunks.includes(0) && (!audioRef.current.src || audioRef.current.src === window.location.href) && !isPlaying && isGenerating) {
        playChunk(0, status)
      }
      if (status.status === 'completed') {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
        setIsGenerating(false)
        
        // Save the audiobook ID to localStorage so this browser session owns it
        if (status.audiobook_id) {
          try {
            const generatedIds = JSON.parse(localStorage.getItem('ink_voice_generated_ids') || '[]')
            if (!generatedIds.includes(status.audiobook_id)) {
              generatedIds.push(status.audiobook_id)
              localStorage.setItem('ink_voice_generated_ids', JSON.stringify(generatedIds))
            }
          } catch (e) {
            console.error("Failed to save audiobook ID to localStorage:", e)
          }
        }

        if (onGenerationComplete) onGenerationComplete()
      } else if (status.status === 'error') {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
        setIsGenerating(false)
        alert(`Generation Error: ${status.error_message}`)
      }
    } catch (e) {
      console.error("Polling error:", e)
    }
  }

  // Handle Playback of a specific chunk
  const playChunk = (chunkIdx, currentStatus = generationStatus) => {
    if (!sessionId) return
    const status = currentStatus || generationStatus
    if (!status) return

    // Set current chunk index immediately to update player state
    setCurrentChunkIdx(chunkIdx)

    // Check if chunk is completed
    if (!status.completed_chunks.includes(chunkIdx)) {
      setIsBuffering(true)
      setIsPlaying(false)
      audioRef.current.pause()
      
      // Unlock the audio element for future async playbacks on this user interaction
      try {
        audioRef.current.src = "data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAAA"
        audioRef.current.play().then(() => audioRef.current.pause()).catch(() => {})
      } catch (e) {}
      
      return
    }
    
    setIsBuffering(false)
    
    // If it's already playing this exact chunk, don't interrupt
    const targetSrc = `${window.location.origin}/api/audio/chunk/${sessionId}/${chunkIdx}`
    if (audioRef.current.src === targetSrc && isPlaying) {
      return
    }

    // Pause current audio playback
    audioRef.current.pause()

    // Reset handlers to avoid closure memory issues
    audioRef.current.onloadedmetadata = null
    audioRef.current.ontimeupdate = null
    audioRef.current.onended = null

    // Load new source
    audioRef.current.src = `/api/audio/chunk/${sessionId}/${chunkIdx}`
    audioRef.current.volume = volume

    // Attach new handlers
    audioRef.current.onloadedmetadata = () => {
      setPlaybackDuration(audioRef.current.duration)
    }
    audioRef.current.ontimeupdate = () => {
      setPlaybackTime(audioRef.current.currentTime)
    }
    audioRef.current.onended = () => {
      const nextIdx = chunkIdx + 1
      if (nextIdx < totalChunks) {
        playChunk(nextIdx, status)
      } else {
        setIsPlaying(false)
        setCurrentChunkIdx(0)
        setPlaybackTime(0)
        audioRef.current.src = "" // Reset src so clicking play restarts from the beginning
      }
    }

    audioRef.current.play()
      .then(() => setIsPlaying(true))
      .catch(e => console.error("Playback failed:", e))
  }

  // Volume change
  const handleVolumeChange = (newVol) => {
    setVolume(newVol)
    if (audioRef.current) audioRef.current.volume = newVol
  }

  // Toggle Play / Pause
  const togglePlayPause = () => {
    const targetSrc = `${window.location.origin}/api/audio/chunk/${sessionId}/${currentChunkIdx}`
    if (!audioRef.current || !audioRef.current.src || audioRef.current.src === window.location.href || audioRef.current.src !== targetSrc) {
      if (generationStatus) {
        playChunk(currentChunkIdx)
      }
      return
    }
    if (isPlaying) {
      audioRef.current.pause()
      setIsPlaying(false)
    } else {
      audioRef.current.play()
        .then(() => setIsPlaying(true))
        .catch(e => console.error(e))
    }
  }

  // Auto-resume when buffered chunk becomes available
  useEffect(() => {
    if (isBuffering && generationStatus && generationStatus.completed_chunks.includes(currentChunkIdx)) {
      setIsBuffering(false)
      playChunk(currentChunkIdx)
    }
  }, [generationStatus, isBuffering, currentChunkIdx])

  const activeChunk = allChunks[currentChunkIdx] || null

  return (
    <div className="container page-layout">
      {/* 1. HERO SECTION */}
      <section className="hero-wrapper">
        <span className="hero-subtitle">Cinematic Multi-Voice Novel Narration</span>
        <h1 className="hero-title text-gradient-display">
          Give Your Written Stories a Living Voice
        </h1>
        <p className="hero-desc">
          Upload your manuscript to dynamically cast realistic character voices, 
          tailored by age and gender with organic emotional depth.
        </p>

        {/* 2. UPLOAD ZONE */}
        {!sessionId && !isAnalyzing && (
          <div className="upload-zone" onDragOver={handleDragOver} onDrop={handleDrop}
            onClick={() => document.getElementById('novel-upload').click()}>
            <span className="upload-icon">✦</span>
            <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>Drop your manuscript here</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '20px' }}>
              PDF, DOCX, or TXT formats
            </p>
            <input id="novel-upload" type="file" accept=".pdf,.docx,.txt" style={{ display: 'none' }} onChange={handleFileChange} />
            <button className="btn-secondary" onClick={(e) => { e.stopPropagation(); document.getElementById('novel-upload').click(); }}>Browse Files</button>
          </div>
        )}

        {/* 3. PARSING STEPS */}
        {isAnalyzing && (
          <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto', padding: '32px' }}>
            <span className="spinner"></span>
            <h3 style={{ fontSize: '18px', marginBottom: '24px' }}>Analyzing Novel Structure</h3>
            <div className="progress-steps">
              {['Extracting document pages…', 'Isolating character dialogues…', 'Analyzing speakers & emotions…', 'Mapping voice profiles…'].map((step, idx) => (
                <div key={idx} className={`step-item ${analysisStep === idx ? 'active' : ''} ${analysisStep > idx ? 'completed' : ''}`}>
                  <span className="step-circle">{analysisStep > idx ? '✓' : idx + 1}</span>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* 4. CHARACTER VOICE CONFIGURATION */}
      {sessionId && (
        <section className="card-row" style={{ animation: 'fadeIn 0.5s ease' }}>
          <div className="glass-panel" style={{ padding: '36px', marginBottom: '40px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <h2 style={{ fontSize: '24px', marginBottom: '6px' }}>Voice Casting Room</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
                  Assign tailored vocal personas to represent each speaker on stage.
                </p>
              </div>
            </div>

            <div className="character-grid">
              {characters.map(char => {
                const charConfig = voicesConfig[char.name] || { gender: 'Female', ageGroup: 'Mid-Age', voice: '1' }
                const isNarrator = char.name === 'Narrator'
                const isFemale = charConfig.gender === 'Female'
                const isLocked = isGenerating || (generationStatus && generationStatus.status !== 'pending')

                // Build voice options
                const voiceOptions = isNarrator
                  ? NARRATOR_VOICES
                  : getCharacterVoices(charConfig.gender, charConfig.ageGroup).map(v => ({ id: v.id, name: v.name }))

                return (
                  <div key={char.name} className="glass-panel character-card" style={{ background: 'rgba(255,255,255,0.01)' }}>
                    <span className={`char-badge ${isNarrator ? 'female' : isFemale ? 'female' : 'male'}`}
                      style={{ background: isNarrator ? 'var(--primary-glow)' : '' }}>
                      {isNarrator ? 'narrator' : `actor · ${charConfig.gender.toLowerCase()}`}
                    </span>

                    <div className={`char-avatar ${isNarrator ? 'narrator' : isFemale ? 'female' : 'male'}`}>
                      {char.name.charAt(0)}
                    </div>

                    <h3 className="char-name">{char.name}</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '16px' }}>
                      {isNarrator ? 'Delivers narrative prose' : `Speaks ${char.mentions} lines of dialogue`}
                    </p>

                    {/* Gender & Age Selectors (characters only) */}
                    {!isNarrator && (
                      <div style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
                        <div style={{ flex: 1 }}>
                          <span className="voice-label">Gender</span>
                          <select className="voice-select" value={charConfig.gender} disabled={isLocked}
                            onChange={(e) => handleCharVoiceChange(char.name, 'gender', e.target.value)}>
                            <option value="Female">Female</option>
                            <option value="Male">Male</option>
                          </select>
                        </div>
                        <div style={{ flex: 1 }}>
                          <span className="voice-label">Age Group</span>
                          <select className="voice-select" value={charConfig.ageGroup} disabled={isLocked}
                            onChange={(e) => handleCharVoiceChange(char.name, 'ageGroup', e.target.value)}>
                            <option value="Young">Child / Young</option>
                            <option value="Mid-Age">Mid-Age</option>
                            <option value="Senior">Senior</option>
                          </select>
                        </div>
                      </div>
                    )}

                    {/* Voice Picker */}
                    <div className="voice-select-wrapper">
                      <span className="voice-label">{isNarrator ? 'Vocal Profile' : 'Selected Voice'}</span>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <select className="voice-select" style={{ flexGrow: 1 }} value={charConfig.voice} disabled={isLocked}
                          onChange={(e) => handleCharVoiceChange(char.name, 'voice', e.target.value)}>
                          {voiceOptions.map(opt => (
                            <option key={opt.id} value={opt.id}>{opt.name}</option>
                          ))}
                        </select>
                        <button className="btn-secondary" onClick={() => playVoicePreview(char.name)}
                          style={{ padding: '8px 12px' }} title="Listen Voice Preview">🔊</button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {!isGenerating && (!generationStatus || generationStatus.status === 'pending') && (
              <div style={{ display: 'flex', justifyContent: 'center', marginTop: '36px' }}>
                <button className="btn-primary" style={{ padding: '14px 32px', fontSize: '16px' }} onClick={startAudiobookGeneration}>
                  Commence Vocal Synthesis ✧
                </button>
              </div>
            )}
          </div>
        </section>
      )}

      {/* 5. RENDERING & PLAYBACK */}
      {generationStatus && (
        <section ref={productionSectionRef} className="card-row" style={{ animation: 'fadeInUp 0.6s ease' }}>
          <div className="glass-panel" style={{ padding: '36px' }}>
            <h2 style={{ fontSize: '24px', marginBottom: '16px' }}>
              {generationStatus.status === 'completed' ? '✓ Stage Play Compiled' : 'Acoustic Stage in Production'}
            </h2>

            {/* Overall progress */}
            <div style={{ marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                <span>Synthesizing neural voices…</span>
                <span>{generationStatus.progress}% ({generationStatus.completed_chunks.length}/{generationStatus.total_chunks})</span>
              </div>
              <div className="progress-bar-bg" style={{ height: '8px' }}>
                <div className="progress-bar-fill" style={{ width: `${generationStatus.progress}%`, background: 'var(--secondary-gradient)' }}></div>
              </div>
            </div>

            {/* Audio Player */}
            {generationStatus.completed_chunks.length > 0 && (
              <div className="audio-player-panel" style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.05)' }}>
                
                {/* Live subtitle with buffering display */}
                {isBuffering ? (
                  <div className="subtitle-box" style={{ opacity: 0.6 }}>
                    <span className="spinner-small" style={{
                      width: '16px', height: '16px', border: '2px solid rgba(138,43,226,0.15)',
                      borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.8s linear infinite',
                      display: 'inline-block', marginRight: '10px'
                    }}></span>
                    <span style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '14px' }}>
                      Synthesizing next line... Please hold.
                    </span>
                  </div>
                ) : activeChunk ? (
                  <div className="subtitle-box">
                    <span className="subtitle-speaker" style={{
                      color: activeChunk.speaker === 'Narrator' ? 'var(--primary)' :
                        voicesConfig[activeChunk.speaker]?.gender === 'Female' ? '#ec4899' : '#3b82f6'
                    }}>
                      {activeChunk.speaker}
                      <span style={{ fontSize: '11px', opacity: 0.8, marginLeft: '8px', fontWeight: 600, letterSpacing: '0.05em' }}>
                        {activeChunk.emotion === 'joy' ? '✧ Joyful' : activeChunk.emotion === 'sad' ? '✧ Sorrowful' : activeChunk.emotion === 'angry' ? '✧ Intense' : '✧ Expressive'}
                      </span>
                    </span>
                    <span style={{ fontStyle: activeChunk.type === 'dialogue' ? 'italic' : 'normal', color: 'var(--text-main)' }}>
                      "{activeChunk.text}"
                    </span>
                  </div>
                ) : null}

                <div className="player-main">
                  <div className={`player-art ${isPlaying ? 'playing' : ''}`}>📖</div>
                  <div className="player-info">
                    <h3 className="player-title" style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}>{title}</h3>
                    <p className="player-subtitle">
                      {isBuffering ? 'Buffering next segment…' : isPlaying ? `Segment ${currentChunkIdx + 1} of ${totalChunks}` : 'Paused'}
                    </p>
                    {generationStatus.generation_time && (
                      <span style={{ 
                        fontSize: '10px', 
                        color: 'var(--accent)', 
                        background: 'rgba(0, 242, 254, 0.08)',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        display: 'inline-block',
                        marginTop: '6px',
                        fontWeight: 600,
                        border: '1px solid rgba(0, 242, 254, 0.15)'
                      }}>
                        ✧ Synthesized in {generationStatus.generation_time}s
                      </span>
                    )}
                  </div>
                  
                  <div className="player-controls">
                    <button className="btn-secondary" onClick={() => playChunk(Math.max(0, currentChunkIdx - 1))}
                      disabled={currentChunkIdx === 0}
                      style={{ borderRadius: '50%', width: '40px', height: '40px', justifyContent: 'center' }}>⏮️</button>
                    <button className="btn-play-pause" onClick={togglePlayPause}>{isPlaying ? '⏸️' : '▶️'}</button>
                    <button className="btn-secondary" onClick={() => playChunk(Math.min(totalChunks - 1, currentChunkIdx + 1))}
                      disabled={currentChunkIdx >= generationStatus.completed_chunks.length}
                      style={{ borderRadius: '50%', width: '40px', height: '40px', justifyContent: 'center' }}>⏭️</button>
                  </div>
                </div>

                {/* Seek bar */}
                <div className="progress-container">
                  <span>{formatTime(playbackTime)}</span>
                  <div className="progress-bar-bg" onClick={(e) => {
                    if (!audioRef.current) return
                    const rect = e.currentTarget.getBoundingClientRect()
                    audioRef.current.currentTime = ((e.clientX - rect.left) / rect.width) * audioRef.current.duration
                  }}>
                    <div className="progress-bar-fill" style={{ width: `${playbackDuration > 0 ? (playbackTime / playbackDuration) * 100 : 0}%` }}></div>
                  </div>
                  <span>{formatTime(playbackDuration)}</span>
                </div>

                {/* Volume + Download row */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', flexWrap: 'wrap', gap: '16px' }}>
                  
                  {/* Volume Slider */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: '1 1 280px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '16px', cursor: 'pointer' }} onClick={() => handleVolumeChange(volume > 0 ? 0 : 0.85)}>
                      {volume === 0 ? '🔇' : volume < 0.4 ? '🔈' : volume < 0.7 ? '🔉' : '🔊'}
                    </span>
                    <input
                      type="range" min="0" max="1" step="0.01" value={volume}
                      onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                      className="volume-slider"
                      style={{
                        width: '140px', height: '4px', appearance: 'none', WebkitAppearance: 'none',
                        background: `linear-gradient(to right, var(--primary) ${volume * 100}%, rgba(255,255,255,0.12) ${volume * 100}%)`,
                        borderRadius: '2px', outline: 'none', cursor: 'pointer',
                      }}
                    />
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', minWidth: '30px' }}>
                      {Math.round(volume * 100)}%
                    </span>
                    {generationStatus.generation_time && (
                      <span style={{ 
                        fontSize: '11px', 
                        color: 'var(--accent)', 
                        marginLeft: '15px',
                        fontWeight: 600,
                        whiteSpace: 'nowrap'
                      }}>
                        ⏱️ Synthesis & Stitch: {generationStatus.generation_time}s
                      </span>
                    )}
                  </div>

                  {/* Download Buttons */}
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    {/* Download current chunk */}
                    <a href={`/api/audio/chunk/${sessionId}/${currentChunkIdx}`} download={`chunk_${currentChunkIdx}.wav`}
                      className="btn-secondary" style={{ fontSize: '12px', padding: '8px 14px' }}>
                      ⬇ Chunk
                    </a>

                    {/* Download full audiobook (only when complete) */}
                    {generationStatus.status === 'completed' && (
                      <a href={`/api/audio/file/${generationStatus.audiobook_id}`}
                        download={`${title || 'audiobook'}.wav`}
                        className="btn-primary" style={{ fontSize: '13px', padding: '10px 20px' }}>
                        💾 Download Full Audiobook
                      </a>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  )
}

function formatTime(secs) {
  if (isNaN(secs)) return '0:00'
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m}:${s < 10 ? '0' : ''}${s}`
}

export default Home
