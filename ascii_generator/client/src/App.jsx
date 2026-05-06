import { useState, useRef, useEffect } from 'react'
import './App.css'

export default function App() {
  const [prompt, setPrompt] = useState('')
  const [width, setWidth] = useState(80)
  const [charset, setCharset] = useState('dark')
  const [style, setStyle] = useState('lovecraftian')
  const [enhance, setEnhance] = useState(false)

  const [asciiArt, setAsciiArt] = useState('')
  const [imageBase64, setImageBase64] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [charsets, setCharsets] = useState([])
  const [styles, setStyles] = useState([])

  const asciiRef = useRef(null)

  // Load available charsets and styles on mount
  useEffect(() => {
    Promise.all([
      fetch('/api/charsets').then(r => r.json()),
      fetch('/api/styles').then(r => r.json()),
    ]).then(([charsetsData, stylesData]) => {
      setCharsets(charsetsData.charsets || [])
      setStyles(stylesData.styles || [])
    }).catch(err => {
      console.error('Failed to load config:', err)
      setCharsets(['dark', 'detailed', 'blocks', 'standard', 'artistic'])
      setStyles(['lovecraftian', 'standard'])
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
    setImageBase64('')

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt.trim(),
          width: parseInt(width),
          charset,
          style,
          enhance,
        }),
      })

      const data = await response.json()

      if (!data.success) {
        setError(data.error || 'Error generating ASCII art')
        return
      }

      setAsciiArt(data.ascii_art)
      setImageBase64(data.image_base64)

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
        <p className="subtitle">Lovecraftian Horror Edition</p>
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
                rows={4}
                disabled={loading}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="width">Ancho ASCII:</label>
                <input
                  id="width"
                  type="range"
                  min="40"
                  max="120"
                  step="10"
                  value={width}
                  onChange={(e) => setWidth(e.target.value)}
                  disabled={loading}
                />
                <span className="value-display">{width} chars</span>
              </div>

              <div className="form-group">
                <label htmlFor="charset">Charset:</label>
                <select
                  id="charset"
                  value={charset}
                  onChange={(e) => setCharset(e.target.value)}
                  disabled={loading}
                >
                  {charsets.map(cs => (
                    <option key={cs} value={cs}>{cs}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
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

              <div className="form-group checkbox">
                <label>
                  <input
                    type="checkbox"
                    checked={enhance}
                    onChange={(e) => setEnhance(e.target.checked)}
                    disabled={loading}
                  />
                  Mejorar con bordes
                </label>
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
          <h2>Resultados</h2>

          {asciiArt && (
            <>
              {imageBase64 && (
                <div className="image-preview">
                  <h3>Imagen generada:</h3>
                  <img src={imageBase64} alt="Generated scene" />
                </div>
              )}

              <div className="ascii-container">
                <h3>ASCII Art:</h3>
                <pre className="ascii-art">{asciiArt}</pre>
                <button
                  className="btn btn-secondary"
                  onClick={handleDownloadASCII}
                >
                  💾 Descargar ASCII
                </button>
              </div>
            </>
          )}

          {!asciiArt && !loading && (
            <div className="placeholder">
              <p>👈 Completa el formulario y haz clic en generar</p>
            </div>
          )}

          {loading && (
            <div className="loading">
              <div className="spinner"></div>
              <p>Generando imagen y convirtiendo a ASCII...</p>
              <p className="loading-hint">(Esto puede tomar 30-60 segundos)</p>
            </div>
          )}
        </div>
      </main>

      <footer className="footer">
        <p>🖤 ASCII Art Generator • Powered by Stable Diffusion XL + HuggingFace</p>
      </footer>
    </div>
  )
}
