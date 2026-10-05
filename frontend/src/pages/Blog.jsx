import React from 'react'

function Blog() {
  const posts = [
    {
      id: 1,
      title: 'The Art of Lit-Casting: Transforming Prose Into Performance',
      category: 'LITERARY & TECH',
      date: 'May 2026',
      readTime: '4 min read',
      excerpt: 'Exploring the cultural shift of auditory storytelling, where manuscripts become living ensemble plays for modern, high-speed lifestyles.',
      body: 'In an increasingly fast-paced world, carving out uninterrupted hours to read print has become a rare luxury. However, our appetite for immersive narratives remains. "Lit-Casting" bridges this gap by turning static text into organic, multi-voice acoustic dramas. By assigning unique emotional identities to character actors, a novel ceases to be silent; it becomes an active stage play. Whether during a daily commute or quiet evening, literature now walks beside you, fluid and alive.'
    },
    {
      id: 2,
      title: 'Studio Acoustics on Desktop: The Power of Local ONNX Runtimes',
      category: 'NEURAL AUDIO',
      date: 'May 2026',
      readTime: '6 min read',
      excerpt: 'How optimized graph inference enables studio-grade neural speech synthesis locally on standard consumer computers.',
      body: 'Running realistic neural text-to-speech historically demanded heavy GPU servers, massive datasets, and high memory footprints that crashed typical consumer hardware. The optimization of Kokoro-82M changes the playing field. Fitting into under 82MB of space and utilizing compiled ONNX graph executions, it bypasses heavy PyTorch runtimes entirely. This allows standard PCs to run real-time, emotional human inflections offline, providing complete privacy and instant vocal casting.'
    },
    {
      id: 3,
      title: 'Writing for the Auditory Stage: Crafting Prose for Neural Voices',
      category: 'CREATIVE WRITING',
      date: 'May 2026',
      readTime: '5 min read',
      excerpt: 'Tips for formatting dialogue tags, speaker proximity, and semantic emotions for next-generation speech engines.',
      body: 'When authors draft a manuscript, they write primarily for the eye. Yet, as speech synthesis becomes the primary medium for story consumption, writing for the ear is becoming a crucial technique. Structuring dialogue blocks so the speaker is identified early (e.g., "Julian laughed, \'Unbelievable.\'" rather than "\'Unbelievable,\' said Julian after a long sigh") dramatically boosts local NLP classification speed and voice mapping accuracy, resulting in a seamless, theatrical audiobook experience.'
    }
  ]

  return (
    <div className="container page-layout" style={{ animation: 'fadeIn 0.5s ease' }}>
      {/* Hero Header */}
      <section className="hero-wrapper" style={{ padding: '120px 0 40px' }}>
        <span className="hero-subtitle">The Chronicle Shelf</span>
        <h1 className="hero-title text-gradient-display" style={{ fontSize: '42px', marginBottom: '16px' }}>
          The Acoustic Chronicle
        </h1>
        <p className="hero-desc" style={{ fontSize: '15px', maxWidth: '600px', margin: '0 auto' }}>
          Perspectives on the intersection of deep learning, creative literature, and offline audio synthesis.
        </p>
      </section>

      {/* Editorial Posts Stack */}
      <section style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '40px',
        maxWidth: '800px',
        margin: '40px auto 60px'
      }}>
        {posts.map(post => (
          <article 
            key={post.id} 
            className="glass-panel" 
            style={{ 
              padding: '36px',
              background: 'linear-gradient(180deg, rgba(20, 20, 32, 0.4) 0%, rgba(10, 10, 16, 0.7) 100%)',
              borderColor: 'rgba(255,255,255,0.03)'
            }}
          >
            {/* Meta Row */}
            <div style={{ display: 'flex', gap: '14px', alignItems: 'center', fontSize: '11px', color: 'var(--primary)', marginBottom: '16px', fontWeight: 700, letterSpacing: '0.08em' }}>
              <span style={{ background: 'var(--primary-glow)', padding: '4px 10px', borderRadius: '4px' }}>
                {post.category}
              </span>
              <span style={{ color: 'var(--text-muted)' }}>•</span>
              <span style={{ color: 'var(--text-muted)' }}>{post.date}</span>
              <span style={{ color: 'var(--text-muted)' }}>•</span>
              <span style={{ color: 'var(--text-muted)' }}>{post.readTime}</span>
            </div>

            {/* Title */}
            <h2 style={{ fontSize: '24px', marginBottom: '16px', lineHeight: '1.3', fontFamily: 'var(--font-display)', fontWeight: 700 }}>
              {post.title}
            </h2>

            {/* Excerpt */}
            <p style={{ color: 'var(--accent)', fontSize: '14px', lineHeight: '1.6', marginBottom: '16px', fontWeight: 500 }}>
              {post.excerpt}
            </p>
            
            {/* Body */}
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', lineHeight: '1.7' }}>
              {post.body}
            </p>
          </article>
        ))}
      </section>
    </div>
  )
}

export default Blog
