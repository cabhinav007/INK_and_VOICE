import React, { useState, useEffect, useRef } from 'react'

function History({ refreshTrigger, active }) {
  const [audiobooks, setAudiobooks] = useState([])
  const [loading, setLoading] = useState(true)
  
  // In-page playing state
  const [activeAudiobook, setActiveAudiobook] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackTime, setPlaybackTime] = useState(0)
  const [playbackDuration, setPlaybackDuration] = useState(0)
  const [volume, setVolume] = useState(0.85)

  const audioRef = useRef(new Audio())

  // Find the active passage segment based on timing
  const activePassage = activeAudiobook?.passages?.find(
    p => playbackTime >= p.start && playbackTime <= p.end
  ) || null

  // Fetch audiobook catalog
  const fetchAudiobooks = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/audiobooks')
      if (response.ok) {
        const data = await response.json()
        
        // Load allowed IDs from localStorage
        try {
          const generatedIds = JSON.parse(localStorage.getItem('ink_voice_generated_ids') || '[]')
          const filteredData = data.filter(book => generatedIds.includes(book.id))
          setAudiobooks(filteredData)
        } catch (storageErr) {
          console.error("Error reading localStorage:", storageErr)
          setAudiobooks([])
        }
      }
    } catch (e) {
      console.error("Failed to load catalog:", e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAudiobooks()
    
    // Clean up player on unmount
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.src = ""
      }
    }
  }, [refreshTrigger, active])

  // Play compiled master WAV audiobook
  const playMasterAudio = (book) => {
    if (activeAudiobook?.id === book.id) {
      if (isPlaying) {
        audioRef.current.pause()
        setIsPlaying(false)
      } else {
        audioRef.current.play()
          .then(() => setIsPlaying(true))
          .catch(e => console.error(e))
      }
      return
    }

    // Pause current audio
    audioRef.current.pause()

    // Reset handlers to avoid closure memory issues
    audioRef.current.onloadedmetadata = null
    audioRef.current.ontimeupdate = null
    audioRef.current.onended = null

    setActiveAudiobook(book)
    setPlaybackTime(0)
    setPlaybackDuration(0)

    // Load new source
    audioRef.current.src = `/api/audio/file/${book.id}`
    audioRef.current.volume = volume

    // Attach new handlers
    audioRef.current.onloadedmetadata = () => {
      setPlaybackDuration(audioRef.current.duration)
    }
    audioRef.current.ontimeupdate = () => {
      setPlaybackTime(audioRef.current.currentTime)
    }
    audioRef.current.onended = () => {
      setIsPlaying(false)
      setPlaybackTime(0)
      audioRef.current.src = "" // Reset src so next play starts from beginning
    }

    audioRef.current.play()
      .then(() => setIsPlaying(true))
      .catch(e => console.error("Master play failed:", e))
  }

  // Toggle in-page player
  const togglePlayPause = () => {
    if (!activeAudiobook) return
    const targetSrc = `${window.location.origin}/api/audio/file/${activeAudiobook.id}`
    if (!audioRef.current || !audioRef.current.src || audioRef.current.src === window.location.href || audioRef.current.src !== targetSrc) {
      playMasterAudio(activeAudiobook)
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

  // Volume change
  const handleVolumeChange = (newVol) => {
    setVolume(newVol)
    if (audioRef.current) {
      audioRef.current.volume = newVol
    }
  }

  // Skip Forward/Backward by neural passages
  const skipBackward = () => {
    if (!audioRef.current || !activeAudiobook?.passages) return
    const t = audioRef.current.currentTime
    const idx = activeAudiobook.passages.findIndex(p => t >= p.start && t <= p.end)
    if (idx > 0) {
      const curPassage = activeAudiobook.passages[idx]
      // If more than 1.5s into current passage, restart it
      if (t - curPassage.start > 1.5) {
        audioRef.current.currentTime = curPassage.start
      } else {
        audioRef.current.currentTime = activeAudiobook.passages[idx - 1].start
      }
    } else if (idx === 0) {
      audioRef.current.currentTime = 0
    } else {
      audioRef.current.currentTime = Math.max(0, t - 5)
    }
  }

  const skipForward = () => {
    if (!audioRef.current || !activeAudiobook?.passages) return
    const t = audioRef.current.currentTime
    const idx = activeAudiobook.passages.findIndex(p => t >= p.start && t <= p.end)
    if (idx >= 0 && idx < activeAudiobook.passages.length - 1) {
      audioRef.current.currentTime = activeAudiobook.passages[idx + 1].start
    } else {
      audioRef.current.currentTime = Math.min(audioRef.current.duration || 0, t + 5)
    }
  }

  // Delete Audiobook
  const handleDeleteBook = async (e, audiobookId) => {
    e.stopPropagation() // Prevent trigger click play
    if (!window.confirm("Are you sure you want to delete this audiobook from your local library?")) return

    try {
      const response = await fetch(`/api/audiobooks/${audiobookId}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        if (activeAudiobook?.id === audiobookId) {
          if (audioRef.current) {
            audioRef.current.pause()
            audioRef.current.src = ""
            audioRef.current = null
          }
          setActiveAudiobook(null)
          setIsPlaying(false)
        }
        
        // Also remove from localStorage!
        try {
          const generatedIds = JSON.parse(localStorage.getItem('ink_voice_generated_ids') || '[]')
          const updatedIds = generatedIds.filter(id => id !== audiobookId)
          localStorage.setItem('ink_voice_generated_ids', JSON.stringify(updatedIds))
        } catch (storageErr) {
          console.error("Failed to update localStorage after delete:", storageErr)
        }

        fetchAudiobooks()
      } else {
        alert("Failed to delete record.")
      }
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="container page-layout" style={{ animation: 'fadeIn 0.5s ease' }}>
      <section className="hero-wrapper" style={{ padding: '120px 0 40px' }}>
        <span className="hero-subtitle">Vocal Shelf</span>
        <h1 className="hero-title text-gradient-display" style={{ fontSize: '42px', marginBottom: '16px' }}>
          Your Library Archive
        </h1>
        <p className="hero-desc" style={{ fontSize: '15px', maxWidth: '600px', margin: '0 auto 20px' }}>
          Stream or download compiled masterpieces from your vocal stage history.
        </p>
      </section>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <span className="spinner"></span>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '12px' }}>Loading shelf catalog...</p>
        </div>
      ) : audiobooks.length === 0 ? (
        <div className="glass-panel" style={{ padding: '60px 24px', textAlignment: 'center', textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
          <span style={{ fontSize: '48px', display: 'block', marginBottom: '16px' }}>📚</span>
          <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>No chronicles on your shelf yet</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
            Visit the stage to upload a manuscript and initiate synthesis!
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
          {/* Active play header */}
          {activeAudiobook && (
            <div className="glass-panel audio-player-panel" style={{ 
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(16, 16, 26, 0.7) 100%)',
              border: '1px solid rgba(99,102,241,0.2)',
              animation: 'fadeInDown 0.4s ease'
            }}>
              
              {/* Subtitles Display in Library Player */}
              {activePassage && (
                <div className="subtitle-box" style={{ marginBottom: '20px', background: 'rgba(0,0,0,0.4)' }}>
                  <span className="subtitle-speaker" style={{
                    color: activePassage.speaker === 'Narrator' ? 'var(--primary)' : '#ec4899'
                  }}>
                    {activePassage.speaker}
                    <span style={{ fontSize: '11px', opacity: 0.8, marginLeft: '8px', fontWeight: 600, letterSpacing: '0.05em' }}>
                      {activePassage.emotion === 'joy' ? '✧ Joyful' : activePassage.emotion === 'sad' ? '✧ Sorrowful' : activePassage.emotion === 'angry' ? '✧ Intense' : '✧ Expressive'}
                    </span>
                  </span>
                  <span style={{ fontStyle: activePassage.speaker !== 'Narrator' ? 'italic' : 'normal', color: 'var(--text-main)' }}>
                    "{activePassage.text}"
                  </span>
                </div>
              )}
              
              <div className="player-main">
                <div className={`player-art ${isPlaying ? 'playing' : ''}`}>
                  🎵
                </div>

                <div className="player-info">
                  <h3 className="player-title">{activeAudiobook.title}</h3>
                  <p className="player-subtitle">
                    {isPlaying ? 'Playing from Library Archive' : 'Paused'}
                  </p>
                </div>

                <div className="player-controls">
                  <button className="btn-secondary" onClick={skipBackward}
                    style={{ borderRadius: '50%', width: '40px', height: '40px', justifyContent: 'center' }}>⏮️</button>
                  <button className="btn-play-pause" onClick={togglePlayPause}>
                    {isPlaying ? '⏸️' : '▶️'}
                  </button>
                  <button className="btn-secondary" onClick={skipForward}
                    style={{ borderRadius: '50%', width: '40px', height: '40px', justifyContent: 'center' }}>⏭️</button>
                </div>
              </div>

              <div className="progress-container">
                <span>{formatTime(playbackTime)}</span>
                <div 
                  className="progress-bar-bg" 
                  onClick={(e) => {
                    if (!audioRef.current) return
                    const rect = e.currentTarget.getBoundingClientRect()
                    const pct = (e.clientX - rect.left) / rect.width
                    audioRef.current.currentTime = pct * audioRef.current.duration
                  }}
                >
                  <div 
                    className="progress-bar-fill" 
                    style={{ width: `${playbackDuration > 0 ? (playbackTime / playbackDuration) * 100 : 0}%` }}
                  ></div>
                </div>
                <span>{formatTime(playbackDuration)}</span>
              </div>
              
              {/* Volume adjust slider (matching Home player) */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px', flexWrap: 'wrap', gap: '16px' }}>
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
                  {activeAudiobook.generation_time && (
                    <span style={{ 
                      fontSize: '11px', 
                      color: 'var(--accent)', 
                      marginLeft: '15px',
                      fontWeight: 600,
                      whiteSpace: 'nowrap'
                    }}>
                      ⏱️ Synthesis & Stitch: {activeAudiobook.generation_time}s
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Book Catalog Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '24px'
          }}>
            {audiobooks.map(book => {
              const isActive = activeAudiobook?.id === book.id
              const isThisPlaying = isActive && isPlaying

              return (
                <div 
                  key={book.id} 
                  className="glass-panel" 
                  onClick={() => playMasterAudio(book)}
                  style={{
                    padding: '24px',
                    cursor: 'pointer',
                    borderColor: isActive ? 'var(--primary)' : '',
                    background: isActive ? 'rgba(99,102,241,0.03)' : '',
                    position: 'relative'
                  }}
                >
                  {/* Title */}
                  <h3 style={{ fontSize: '18px', marginBottom: '8px', paddingRight: '30px', wordBreak: 'break-word' }}>
                    {book.title}
                  </h3>

                  {/* Play Overlay Badge */}
                  <div style={{
                    position: 'absolute',
                    top: '20px',
                    right: '20px',
                    fontSize: '18px',
                    color: isActive ? 'var(--primary)' : 'var(--text-muted)'
                  }}>
                    {isThisPlaying ? '⏸️' : '▶️'}
                  </div>

                  <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginBottom: '16px' }}>
                    Compiled on {new Date(book.date).toLocaleDateString()}
                    {book.generation_time && ` · Synthesized in ${book.generation_time}s`}
                  </p>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '16px' }}>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Duration: </span>
                      <strong>{formatTime(book.duration)}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Segments: </span>
                      <strong>{book.chunks_count}</strong>
                    </div>
                  </div>

                  {/* Configured characters display */}
                  <div style={{ marginTop: '12px' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Vocal Cast:</span>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {book.characters?.slice(0, 4).map(c => (
                        <span 
                          key={c.name}
                          style={{
                            fontSize: '10px',
                            background: 'rgba(255,255,255,0.05)',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            color: c.name === 'Narrator' ? 'var(--primary)' : 'var(--text-main)'
                          }}
                        >
                          {c.name}
                        </span>
                      ))}
                      {book.characters?.length > 4 && (
                        <span style={{ fontSize: '10px', color: 'var(--text-muted)', alignSelf: 'center' }}>+{book.characters.length - 4} more</span>
                      )}
                    </div>
                  </div>

                  {/* Download and Delete Row */}
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }} onClick={(e) => e.stopPropagation()}>
                    <a 
                      href={`/api/audio/file/${book.id}`}
                      download
                      className="btn-secondary"
                      style={{ fontSize: '11px', padding: '6px 12px' }}
                    >
                      Download (WAV)
                    </a>
                    
                    <button 
                      className="btn-secondary" 
                      onClick={(e) => handleDeleteBook(e, book.id)}
                      style={{ 
                        fontSize: '11px', 
                        padding: '6px 12px',
                        color: 'var(--danger)',
                        borderColor: 'rgba(239, 68, 110, 0.1)',
                        background: 'rgba(239, 68, 110, 0.03)'
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

// Time formatter utility
function formatTime(secs) {
  if (isNaN(secs)) return '0:00'
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m}:${s < 10 ? '0' : ''}${s}`
}

export default History
