import { useState, useRef, useEffect } from 'react'
import './App.css'

export default function App() {
  const [prompt, setPrompt] = useState('')
  const [width, setWidth] = useState(160)
  const [style, setStyle] = useState('lovecraftian')

  const [asciiArt, setAsciiArt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [styles, setStyles] = useState([])

  const asciiRef = useRef(null)

  // Load available styles on mount
  useEffect(() => {
    fetch('/api/styles')
      .then(r => r.json())
      .then(data => setStyles(data.styles || []))
      .catch(err => {
        console.error('Failed to load styles:', err)
        setStyles(['lovecraftian', 'cosmic-horror', 'nature', 'urban', 'fantasy', 'dark-fantasy'])
      })
  }, [])

  const handleGenerate = async (e) => {
    e.preventDefault()

    if (!prompt.trim()) {
      setError('Por favor escribe una descripción')
      return
    }

    setLoading(true)
    setError('')
    setAsciiArt('')

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt.trim(),
          width: parseInt(width),
          style,
        }),
      })

      const data = await response.json()

      if (!data.success) {
        setError(data.error || 'Error generating ASCII art')
        return
      }

      setAsciiArt(data.ascii_art)

      // Scroll to results
      setTimeout(() => {
        asciiRef.current?.scrollIntoView({ behavior: 'smooth' })
      }, 100)

    } catch (err) {
      setError(`Error de conexión: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadASCII = () => {
    const element = document.createElement('a')
    const file = new Blob([asciiArt], { type: 'text/plain' })
    element.href = URL.createObjectURL(file)
    element.download = 'ascii-art.txt'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🎨 ASCII Art Generator</h1>
        <p className="subtitle">Lovecraftian Horror Edition • Powered by Ollama</p>
      </header>

      <main className="main">
        {/* Left Panel: Controls */}
        <div className="panel controls-panel">
          <h2>Generador</h2>

          <form onSubmit={handleGenerate}>
            <div className="form-group">
              <label htmlFor="prompt">Descripción de la escena:</label>
              <textarea
                id="prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ej: A dark lighthouse on a rocky coast with fog and mysterious symbols on the ground..."
                rows={5}
                disabled={loading}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="width">Ancho ASCII:</label>
                <input
                  id="width"
                  type="range"
                  min="80"
                  max="2000"
                  step="100"
                  value={width}
                  onChange={(e) => setWidth(e.target.value)}
                  disabled={loading}
                />
                <span className="value-display">{width} chars</span>
              </div>

              <div className="form-group">
                <label htmlFor="style">Estilo:</label>
                <select
                  id="style"
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  disabled={loading}
                >
                  {styles.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>

            {error && <div className="error-message">{error}</div>}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !prompt.trim()}
            >
              {loading ? '⏳ Generando...' : '✨ Generar ASCII Art'}
            </button>
          </form>
        </div>

        {/* Right Panel: Results */}
        <div className="panel results-panel" ref={asciiRef}>
          <h2>Resultado</h2>

          {asciiArt && (
            <div className="ascii-container">
              <pre className="ascii-art">{asciiArt}</pre>
              <button
                className="btn btn-secondary"
                onClick={handleDownloadASCII}
              >
                💾 Descargar ASCII
              </button>
            </div>
          )}

          {!asciiArt && !loading && (
            <div className="placeholder">
              <p>👈 Completa el formulario y haz clic en generar</p>
            </div>
          )}

          {loading && (
            <div className="loading">
              <div className="spinner"></div>
              <p>Generando ASCII art con Ollama...</p>
              <p className="loading-hint">(esto puede tomar 10-30 segundos)</p>
            </div>
          )}
        </div>
      </main>

      <footer className="footer">
        <p>🖤 ASCII Art Generator • Powered by Ollama LLM</p>
      </footer>
    </div>
  )
}
