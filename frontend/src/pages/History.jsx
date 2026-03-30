import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, Star, ThumbsUp, ChevronDown, ChevronUp } from 'lucide-react'
import api from '../api/client'

export default function History() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/history').then(r => setData(r.data)).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (!data?.results?.length) return (
    <div className="text-center py-20">
      <p className="text-gray-500 text-lg">No analyses yet.</p>
      <button onClick={() => navigate('/')} className="btn-primary mt-4">Analyse a product</button>
    </div>
  )

  return (
    <div className="animate-fade-in space-y-4 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Analysis History <span className="text-gray-500 text-base font-normal">({data.total})</span></h1>
      {data.results.map(({ analysis, product }, i) => (
        <div key={analysis.id} className="glass overflow-hidden">
          <button
            className="w-full p-5 flex items-center gap-4 text-left hover:bg-white/5 transition-colors"
            onClick={() => setExpanded(expanded === i ? null : i)}
          >
            {product?.image_url && <img src={product.image_url} alt="" className="w-12 h-12 object-contain rounded-lg bg-gray-900 p-1 shrink-0" />}
            <div className="flex-1 min-w-0">
              <p className="font-semibold truncate">{product?.name || 'Unknown Product'}</p>
              <div className="flex items-center gap-3 mt-1 text-sm text-gray-400">
                {product?.price && <span className="text-indigo-400 font-medium">₹{product.price.toLocaleString()}</span>}
                {product?.average_rating && <span className="flex items-center gap-1"><Star className="w-3 h-3 text-amber-400 fill-amber-400" />{product.average_rating}</span>}
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{new Date(analysis.analyzed_at).toLocaleDateString()}</span>
              </div>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <span className="text-sm text-emerald-400 font-medium">{analysis.positive_percentage?.toFixed(0)}% pos</span>
              <span className="text-sm text-gray-400">Trust: {analysis.trust_score?.toFixed(0)}</span>
              {expanded === i ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
            </div>
          </button>
          {expanded === i && (
            <div className="px-5 pb-5 pt-0 border-t border-white/10 text-sm text-gray-400 space-y-2 animate-slide-up">
              {analysis.ai_summary && <p>{analysis.ai_summary}</p>}
              <div className="flex gap-4">
                <span>📊 Sentiment: {analysis.overall_sentiment_score?.toFixed(2)}</span>
                <span>🛡️ Trust: {analysis.trust_score?.toFixed(0)}/100</span>
                <span>💰 Value: {analysis.value_score?.toFixed(0)}/100</span>
              </div>
              <div className="flex items-center gap-2">
                Recommendation:
                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold border badge-${analysis.recommendation}`}>
                  {analysis.recommendation?.toUpperCase()}
                </span>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
