import { useLocation, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from 'recharts'
import { ThumbsUp, ThumbsDown, Star, ShieldCheck, ShieldAlert, TrendingUp, ArrowLeft } from 'lucide-react'
import clsx from 'clsx'

// ── Sub-components ─────────────────────────────────────────────────────────

function ScoreRing({ value, max = 100, label, color = 'indigo' }) {
  const pct = Math.round((value / max) * 100)
  const colors = { indigo: '#6366f1', emerald: '#10b981', amber: '#f59e0b', red: '#ef4444' }
  const stroke = colors[color] || colors.indigo
  const r = 38; const circ = 2 * Math.PI * r
  const offset = circ - (pct / 100) * circ
  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="96" height="96" className="-rotate-90">
        <circle cx="48" cy="48" r={r} strokeWidth="7" stroke="#1f2937" fill="none" />
        <circle cx="48" cy="48" r={r} strokeWidth="7" stroke={stroke} fill="none"
          strokeDasharray={circ} strokeDashoffset={offset}
          className="transition-all duration-700" strokeLinecap="round" />
      </svg>
      <div className="text-center -mt-16">
        <div className="text-2xl font-bold" style={{ color: stroke }}>{value ?? '—'}</div>
      </div>
      <div className="text-sm text-gray-400 mt-8">{label}</div>
    </div>
  )
}

function RecommendationBadge({ rec }) {
  const map = {
    buy:   { label: '✅ Buy',  cls: 'badge-buy' },
    skip:  { label: '❌ Skip', cls: 'badge-skip' },
    maybe: { label: '🤔 Maybe', cls: 'badge-maybe' },
  }
  const { label, cls } = map[rec] || { label: rec, cls: '' }
  return (
    <span className={clsx('px-4 py-1.5 rounded-full text-sm font-semibold border', cls)}>
      {label}
    </span>
  )
}

export default function Results() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const result = state?.result

  useEffect(() => {
    if (!result) navigate('/')
  }, [result, navigate])

  if (!result) return null

  const { product, sentiment, trust, ai_summary, value_analysis, reviews_count } = result

  // Recharts data
  const distData = Object.entries(sentiment.distribution ?? {}).map(([k, v]) => ({
    name: k.replace('_', ' '),
    count: v,
  }))
  const distColors = ['#ef4444', '#f97316', '#eab308', '#84cc16', '#22c55e']

  const aspectData = Object.entries(sentiment.aspects ?? {})
    .filter(([, v]) => v.score !== null)
    .map(([k, v]) => ({ subject: k, score: Math.round((v.score + 1) / 2 * 100), fullMark: 100 }))

  return (
    <div className="animate-fade-in space-y-6">
      {/* Back */}
      <button onClick={() => navigate('/')} className="flex items-center gap-2 text-gray-400 hover:text-gray-100 transition-colors text-sm">
        <ArrowLeft className="w-4 h-4" /> Back to search
      </button>

      {/* Product Header */}
      <div className="glass p-6 flex gap-6 items-start animate-slide-up">
        {product.image_url && (
          <img src={product.image_url} alt={product.name} className="w-28 h-28 object-contain rounded-xl bg-gray-900 p-2 shrink-0" />
        )}
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold text-gray-100 mb-2 line-clamp-2">{product.name || 'Unknown Product'}</h1>
          {product.brand && <p className="text-gray-400 text-sm mb-3">by {product.brand}</p>}
          <div className="flex flex-wrap gap-4">
            {product.price && (
              <div className="flex items-center gap-1">
                <span className="text-2xl font-bold text-indigo-400">₹{product.price.toLocaleString()}</span>
                <span className="text-gray-500 text-sm">{product.currency}</span>
              </div>
            )}
            {product.average_rating && (
              <div className="flex items-center gap-1.5 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-1">
                <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                <span className="text-amber-400 font-semibold">{product.average_rating}</span>
                <span className="text-gray-500 text-sm">/ 5</span>
              </div>
            )}
            <span className="text-gray-500 text-sm self-center">{reviews_count} reviews analysed</span>
          </div>
        </div>
        <RecommendationBadge rec={ai_summary.recommendation} />
      </div>

      {/* Score Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass p-6 flex flex-col items-center">
          <ScoreRing
            value={Math.round((sentiment.overall_score + 1) / 2 * 100)}
            label="Sentiment"
            color={sentiment.overall_score > 0.2 ? 'emerald' : sentiment.overall_score < -0.2 ? 'red' : 'amber'}
          />
        </div>
        <div className="glass p-6 flex flex-col items-center">
          <ScoreRing
            value={Math.round(trust.score)}
            label="Trust Score"
            color={trust.score >= 70 ? 'emerald' : trust.score >= 40 ? 'amber' : 'red'}
          />
        </div>
        <div className="glass p-6 flex flex-col items-center">
          <ScoreRing
            value={Math.round(value_analysis.value_score)}
            label="Value Score"
            color={value_analysis.value_score >= 70 ? 'emerald' : 'indigo'}
          />
        </div>
        <div className="glass p-6 flex flex-col items-center justify-center gap-2 text-center">
          <div className={clsx('text-4xl font-bold', trust.risk_level === 'low' ? 'text-emerald-400' : trust.risk_level === 'medium' ? 'text-amber-400' : 'text-red-400')}>
            {trust.suspicious_count}
          </div>
          <div className="text-gray-400 text-sm">Suspicious Reviews</div>
          <span className={clsx('text-xs px-2 py-0.5 rounded-full', `badge-${trust.risk_level}`)}>
            {trust.risk_level} risk
          </span>
        </div>
      </div>

      {/* Sentiment %% */}
      <div className="grid md:grid-cols-3 gap-4">
        {[
          { label: 'Positive', pct: sentiment.positive_pct, color: 'from-emerald-500 to-green-400', icon: ThumbsUp },
          { label: 'Neutral',  pct: sentiment.neutral_pct,  color: 'from-gray-500 to-gray-400',     icon: null },
          { label: 'Negative', pct: sentiment.negative_pct, color: 'from-red-500 to-rose-400',      icon: ThumbsDown },
        ].map(({ label, pct, color, icon: Icon }) => (
          <div key={label} className="glass p-5">
            <div className="flex justify-between items-center mb-3">
              <span className="text-gray-400 text-sm">{label}</span>
              <span className="font-bold text-xl">{pct?.toFixed(1)}%</span>
            </div>
            <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
              <div className={clsx('h-full bg-gradient-to-r rounded-full transition-all duration-700', color)} style={{ width: `${pct}%` }} />
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Distribution Bar Chart */}
        {distData.length > 0 && (
          <div className="glass p-6">
            <h2 className="text-lg font-semibold mb-4">Sentiment Distribution</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={distData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {distData.map((_, i) => <Cell key={i} fill={distColors[i]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Aspect Radar Chart */}
        {aspectData.length > 2 && (
          <div className="glass p-6">
            <h2 className="text-lg font-semibold mb-4">Aspect Analysis</h2>
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={aspectData}>
                <PolarGrid stroke="#374151" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <Radar name="Score" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* AI Summary */}
      <div className="glass p-6 animate-slide-up">
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <span className="text-2xl">🤖</span> AI Summary
        </h2>
        <p className="text-gray-300 leading-relaxed mb-6">{ai_summary.summary}</p>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold text-emerald-400 flex items-center gap-2 mb-3">
              <ThumbsUp className="w-4 h-4" /> Pros
            </h3>
            <ul className="space-y-2">
              {ai_summary.pros?.map((p, i) => (
                <li key={i} className="flex gap-2 text-sm text-gray-300">
                  <span className="text-emerald-400 mt-0.5">✓</span> {p}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-red-400 flex items-center gap-2 mb-3">
              <ThumbsDown className="w-4 h-4" /> Cons
            </h3>
            <ul className="space-y-2">
              {ai_summary.cons?.map((c, i) => (
                <li key={i} className="flex gap-2 text-sm text-gray-300">
                  <span className="text-red-400 mt-0.5">✗</span> {c}
                </li>
              ))}
            </ul>
          </div>
        </div>
        {ai_summary.recommendation_reason && (
          <div className="mt-4 p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-sm text-indigo-300">
            💡 {ai_summary.recommendation_reason}
          </div>
        )}
        {ai_summary.best_for && (
          <div className="mt-4 grid md:grid-cols-2 gap-4 text-sm">
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
              <span className="font-medium text-emerald-400">Best for:</span> <span className="text-gray-300">{ai_summary.best_for}</span>
            </div>
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
              <span className="font-medium text-red-400">Avoid if:</span> <span className="text-gray-300">{ai_summary.avoid_if}</span>
            </div>
          </div>
        )}
      </div>

      {/* Value & Trust */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="glass p-6">
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-indigo-400" /> Value Analysis
          </h2>
          <p className="text-indigo-300 font-medium capitalize">{value_analysis.price_category} product</p>
          <p className="text-gray-400 text-sm mt-1">{value_analysis.verdict}</p>
        </div>
        <div className="glass p-6">
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            {trust.risk_level === 'low' ? <ShieldCheck className="w-5 h-5 text-emerald-400" /> : <ShieldAlert className="w-5 h-5 text-amber-400" />}
            Review Authenticity
          </h2>
          <p className="text-gray-300 text-sm">
            <span className="font-semibold">{trust.suspicious_count}</span> of {trust.total_analyzed} reviews flagged as suspicious ({trust.suspicious_pct?.toFixed(1)}%).
          </p>
          <p className="text-gray-400 text-sm mt-1">Risk level: <span className={clsx('font-medium', trust.risk_level === 'low' ? 'text-emerald-400' : trust.risk_level === 'medium' ? 'text-amber-400' : 'text-red-400')}>{trust.risk_level}</span></p>
        </div>
      </div>
    </div>
  )
}
