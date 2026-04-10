import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Sparkles, Shield, TrendingUp, Zap } from 'lucide-react'
import api from '../api/client'

const features = [
  { icon: Sparkles,   title: 'AI Summaries',      desc: 'Gemini AI generates pros, cons & buying recommendations' },
  { icon: Shield,     title: 'Fake Detection',     desc: 'ML classifier identifies suspicious & fake reviews' },
  { icon: TrendingUp, title: 'Sentiment Analysis', desc: 'VADER + DistilBERT dual-engine sentiment scoring' },
  { icon: Zap,        title: 'Value Score',         desc: 'Price-to-sentiment ratio reveals true value for money' },
]

export default function Home() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleAnalyse = async (e) => {
    e.preventDefault()
    if (!url.trim()) return
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/analyze', { url: url.trim(), max_reviews: 50 })
      navigate('/results', { state: { result: data } })
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Check the URL and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <div className="text-center py-20 px-4">
        <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1.5 text-indigo-400 text-sm font-medium mb-6">
          <Sparkles className="w-3.5 h-3.5" /> Powered by Gemini AI + ML
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold mb-6 leading-tight">
          <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            AI Product Analyser
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
              placeholder="https://www.amazon.in/dp/B0XXXXXXXX/"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={loading}
            />
            {/* <input
              id="product-url-input"
              type="url"
              className="input flex-1 text-base"
              placeholder="https://www.amazon.in/HaRvic-Tumbler-Stainless-Insulated-Travel/dp/B0XXXXXXXX/"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={loading}
            /> */}
            <button
              id="analyse-btn"
              type="submit"
              className="btn-primary flex items-center gap-2 whitespace-nowrap"
              disabled={loading || !url}
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Analysing…
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" /> Analyse
                </>
              )}
            </button>
          </div>
          {error && (
            <p className="mt-3 text-red-400 text-sm text-left">{error}</p>
          )}
          <p className="mt-3 text-gray-600 text-sm">
            Tip: Works with amazon.in product pages. Analysis takes 1–2 minutes.
          </p>
        </form>
      </div>

      {/* Features Grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 py-8">
        {features.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="glass p-6 hover:bg-white/10 transition-all duration-300 group">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center mb-4 group-hover:bg-indigo-500/30 transition-colors">
              <Icon className="w-5 h-5 text-indigo-400" />
            </div>
            <h3 className="font-semibold text-gray-100 mb-1">{title}</h3>
            <p className="text-sm text-gray-500">{desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
