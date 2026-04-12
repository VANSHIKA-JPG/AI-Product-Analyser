import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Sparkles, Shield, TrendingUp, Zap } from 'lucide-react'
import api from '../api/client'

const features = [
  { icon: Sparkles,   title: 'AI Summaries',      desc: 'Gemini AI generates pros, cons & buying recommendations' },
  { icon: Shield,     title: 'Fake Detection',     desc: 'ML classifier identifies suspicious & fake reviews' },
  { icon: TrendingUp, title: 'Sentiment Analysis', desc: 'VADER + ML dual-engine sentiment scoring' },
  { icon: Zap,        title: 'Value Score',        desc: 'Price-to-sentiment ratio reveals true value for money' },
]

// Loading steps to cycle through while the backend works
const LOADING_STEPS = [
  { icon: '🔍', text: 'Scraping Amazon product page…' },
  { icon: '💬', text: 'Collecting customer reviews…' },
  { icon: '🧠', text: 'Running sentiment analysis…' },
  { icon: '🛡️', text: 'Detecting fake reviews with ML…' },
  { icon: '🤖', text: 'Generating AI summary with Gemini…' },
  { icon: '📊', text: 'Calculating value score…' },
  { icon: '💾', text: 'Saving results to database…' },
  { icon: '✨', text: 'Almost done — finalising results…' },
]

function LoadingOverlay() {
  const [stepIdx, setStepIdx] = useState(0)
  const [dots, setDots] = useState('')

  useEffect(() => {
    // Advance through steps every ~3.5 seconds
    const stepTimer = setInterval(() => {
      setStepIdx(i => Math.min(i + 1, LOADING_STEPS.length - 1))
    }, 3500)
    // Animated dots
    const dotsTimer = setInterval(() => {
      setDots(d => d.length >= 3 ? '' : d + '.')
    }, 500)
    return () => { clearInterval(stepTimer); clearInterval(dotsTimer) }
  }, [])

  const current = LOADING_STEPS[stepIdx]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-brand-navy/95 backdrop-blur-md animate-fade-in">
      <div className="glass p-10 max-w-md w-full mx-4 text-center relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 bg-gradient-to-br from-brand-cyan/5 to-brand-lavender/5 pointer-events-none" />

        {/* Spinner */}
        <div className="relative mx-auto w-20 h-20 mb-8">
          <div className="absolute inset-0 rounded-full border-4 border-white/5" />
          <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-brand-cyan animate-spin" />
          <div className="absolute inset-2 rounded-full border-4 border-transparent border-t-brand-lavender animate-spin" style={{ animationDuration: '1.5s', animationDirection: 'reverse' }} />
          <div className="absolute inset-0 flex items-center justify-center text-2xl">
            {current.icon}
          </div>
        </div>

        <h2 className="text-xl font-bold text-white mb-2">Analysing Product</h2>
        <p className="text-brand-cyan font-medium text-lg mb-6 min-h-[1.75rem] transition-all duration-500">
          {current.text}{dots}
        </p>

        {/* Progress bar */}
        <div className="h-1.5 bg-brand-navy rounded-full overflow-hidden mb-6">
          <div
            className="h-full bg-gradient-to-r from-brand-cyan to-brand-lavender rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${((stepIdx + 1) / LOADING_STEPS.length) * 100}%` }}
          />
        </div>

        {/* Steps list */}
        <div className="space-y-2 text-left">
          {LOADING_STEPS.slice(0, stepIdx + 1).map((step, i) => (
            <div key={i} className={`flex items-center gap-3 text-sm transition-all duration-300 ${i === stepIdx ? 'text-white' : 'text-gray-500'}`}>
              <span className="text-base">{i < stepIdx ? '✅' : step.icon}</span>
              <span>{step.text}</span>
            </div>
          ))}
        </div>

        <p className="mt-6 text-xs text-gray-600">This typically takes 15–30 seconds</p>
      </div>
    </div>
  )
}

export default function Home() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const normalizeAmazonUrl = (raw) => {
    try {
      const u = new URL(raw)
      const match = raw.match(/\/(?:dp|gp\/product|ASIN)\/([A-Z0-9]{10})/i)
      if (match) return `https://${u.hostname}/dp/${match[1]}/`
      return raw
    } catch {
      return raw
    }
  }

  const handleAnalyse = async (e) => {
    e.preventDefault()
    if (!url.trim()) return
    setLoading(true)
    setError('')
    try {
      const cleanUrl = normalizeAmazonUrl(url.trim())
      const { data } = await api.post('/analyze', { url: cleanUrl, max_reviews: 20 })
      navigate('/results', { state: { result: data } })
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please check the URL and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {loading && <LoadingOverlay />}

      <div className="animate-fade-in">
        {/* Hero */}
        <div className="text-center py-20 px-4">
          <div className="inline-flex items-center gap-2 bg-brand-cyan/10 border border-brand-cyan/20 rounded-full px-4 py-1.5 text-brand-cyan text-sm font-medium mb-6 shadow-[0_0_15px_rgba(110,231,249,0.15)]">
            <Sparkles className="w-3.5 h-3.5" /> Powered by Gemini AI + ML
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold mb-6 leading-tight drop-shadow-xl">
            <span className="bg-gradient-to-r from-brand-cyan via-white to-brand-lavender bg-clip-text text-transparent">
              ReviewLens
            </span>
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-12">
            Paste any Amazon product URL to instantly get sentiment analysis, fake review detection,
            AI-powered summaries, and value-for-money scores.
          </p>

          {/* Search */}
          <form onSubmit={handleAnalyse} className="max-w-2xl mx-auto">
            <div className="flex gap-3">
              <input
                id="product-url-input"
                type="url"
                className="input flex-1 text-base"
                placeholder="https://www.amazon.in/dp/B0D79HM1FC/"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading}
              />
              <button
                id="analyse-btn"
                type="submit"
                className="btn-primary flex items-center gap-2 whitespace-nowrap"
                disabled={loading || !url}
              >
                <Search className="w-4 h-4" /> Analyse
              </button>
            </div>
            {error && <p className="mt-3 text-brand-alert text-sm text-left bg-brand-alert/10 border border-brand-alert/20 rounded-lg px-4 py-2">{error}</p>}
            <p className="mt-3 text-gray-600 text-sm">
              Works with amazon.in product pages. Analysis takes ~15–30 seconds.
            </p>
          </form>
        </div>

        {/* Features Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 py-8">
          {features.map(({ icon: Icon, title, desc }, idx) => (
            <div
              key={title}
              className="glass p-6 hover:bg-white/5 transition-all duration-300 group animate-float"
              style={{ animationDelay: `${idx * 0.15}s` }}
            >
              <div className="w-12 h-12 rounded-xl bg-brand-cyan/10 flex items-center justify-center mb-4 group-hover:bg-brand-cyan/20 group-hover:shadow-[0_0_15px_rgba(110,231,249,0.3)] transition-all">
                <Icon className="w-6 h-6 text-brand-cyan" />
              </div>
              <h3 className="font-semibold text-gray-100 mb-2">{title}</h3>
              <p className="text-sm text-gray-400">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
