import { useLocation, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from 'recharts'
import { ThumbsUp, ThumbsDown, Star, ShieldCheck, ShieldAlert, TrendingUp, ArrowLeft, MessageSquare } from 'lucide-react'
import clsx from 'clsx'
import api from '../api/client'

// ── Sub-components ─────────────────────────────────────────────────────────

function ScoreRing({ value, max = 100, label, color = 'cyan' }) {
  const pct = Math.round((value / max) * 100)
  const colors = { 
    cyan: '#6EE7F9', 
    success: '#34D399', 
    amber: '#f59e0b', 
    alert: '#F87171' 
  }
  const stroke = colors[color] || colors.cyan
  const r = 38; const circ = 2 * Math.PI * r
  const offset = circ - (pct / 100) * circ
  return (
    <div className="flex flex-col items-center gap-2 relative">
      <svg width="96" height="96" className="-rotate-90 drop-shadow-[0_0_10px_rgba(110,231,249,0.2)]">
        <circle cx="48" cy="48" r={r} strokeWidth="6" stroke="#1f2937" fill="none" />
        <circle cx="48" cy="48" r={r} strokeWidth="6" stroke={stroke} fill="none"
          strokeDasharray={circ} strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out" strokeLinecap="round" />
      </svg>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center mt-[-10px]">
        <div className="text-2xl font-extrabold" style={{ color: stroke }}>{value ?? '—'}</div>
      </div>
      <div className="text-sm font-medium text-gray-400">{label}</div>
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
    <span className={clsx('px-4 py-1.5 rounded-full text-sm font-bold border', cls)}>
      {label}
    </span>
  )
}

export default function Results() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const result = state?.result
  const [reviews, setReviews] = useState([])
  const [loadingReviews, setLoadingReviews] = useState(true)

  useEffect(() => {
    if (!result) navigate('/')
    else {
      // Fetch the individual reviews from the backend
      api.get(`/analysis/${result.analysis_id}`)
        .then(res => setReviews(res.data.reviews || []))
        .catch(err => console.error("Could not fetch reviews:", err))
        .finally(() => setLoadingReviews(false))
    }
  }, [result, navigate])

  if (!result) return null

  const { product, sentiment, trust, ai_summary, value_analysis, reviews_count } = result

  // Recharts data
  const distData = Object.entries(sentiment.distribution ?? {}).map(([k, v]) => ({
    name: k.replace('_', ' '),
    count: v,
  }))
  // mapping: very_negative, negative, neutral, positive, very_positive
  const distColors = ['#F87171', '#fca5a5', '#eab308', '#6ee7b7', '#34D399']

  const aspectData = Object.entries(sentiment.aspects ?? {})
    .filter(([, v]) => v.score !== null)
    .map(([k, v]) => ({ subject: k, score: Math.round((v.score + 1) / 2 * 100), fullMark: 100 }))

  return (
    <div className="animate-fade-in space-y-6 pb-20">
      {/* Back */}
      <button onClick={() => navigate('/')} className="flex items-center gap-2 text-brand-cyan hover:text-brand-cyanHover hover:underline transition-colors text-sm font-medium">
        <ArrowLeft className="w-4 h-4" /> Back to search
      </button>

      {/* Product Header */}
      <div className="glass p-6 md:p-8 flex flex-col md:flex-row gap-6 items-center md:items-start animate-slide-up relative overflow-hidden">
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-brand-cyan/10 rounded-full blur-3xl pointer-events-none"></div>
        
        {product.image_url && (
          <img src={product.image_url} alt={product.name} className="w-32 h-32 object-contain rounded-2xl bg-white/5 p-3 shrink-0 shadow-inner border border-white/5" />
        )}
        <div className="flex-1 min-w-0 text-center md:text-left z-10">
          <h1 className="text-2xl md:text-3xl font-extrabold text-white mb-2 line-clamp-2">{product.name || 'Unknown Product'}</h1>
          {product.brand && <p className="text-brand-lavender text-sm font-semibold mb-4 uppercase tracking-wider">{product.brand}</p>}
          <div className="flex flex-wrap justify-center md:justify-start items-center gap-4">
            {product.price && (
              <div className="flex items-center gap-1 bg-brand-cyan/10 px-4 py-1.5 rounded-lg border border-brand-cyan/20">
                <span className="text-2xl font-bold text-brand-cyan shadow-brand-cyan/20">₹{product.price.toLocaleString()}</span>
              </div>
            )}
            {product.average_rating && (
              <div className="flex items-center gap-1.5 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-1.5 shadow-[0_0_10px_rgba(245,158,11,0.1)]">
                <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                <span className="text-amber-400 font-bold">{product.average_rating}</span>
                <span className="text-amber-400/60 text-sm">/ 5</span>
              </div>
            )}
            <span className="text-gray-400 text-sm self-center font-medium bg-white/5 px-3 py-1.5 rounded-lg">{reviews_count} reviews analysed</span>
          </div>
        </div>
        <div className="z-10 mt-4 md:mt-0">
          <RecommendationBadge rec={ai_summary.recommendation} />
        </div>
      </div>

      {/* Score Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-slide-up" style={{ animationDelay: '0.1s' }}>
        <div className="glass p-6 flex flex-col items-center justify-center">
          <ScoreRing
            value={Math.round((sentiment.overall_score + 1) / 2 * 100)}
            label="Sentiment"
            color={sentiment.overall_score > 0.2 ? 'success' : sentiment.overall_score < -0.2 ? 'alert' : 'amber'}
          />
        </div>
        <div className="glass p-6 flex flex-col items-center justify-center">
          <ScoreRing
            value={Math.round(trust.score)}
            label="Trust Score"
            color={trust.score >= 70 ? 'success' : trust.score >= 40 ? 'amber' : 'alert'}
          />
        </div>
        <div className="glass p-6 flex flex-col items-center justify-center">
          <ScoreRing
            value={Math.round(value_analysis.value_score)}
            label="Value Score"
            color={value_analysis.value_score >= 70 ? 'success' : 'cyan'}
          />
        </div>
        <div className="glass p-6 flex flex-col items-center justify-center gap-2 text-center relative overflow-hidden">
          <div className={clsx('absolute inset-0 opacity-10 bg-gradient-to-t', trust.risk_level === 'low' ? 'from-brand-success' : trust.risk_level === 'medium' ? 'from-amber-400' : 'from-brand-alert')}></div>
          <div className={clsx('text-5xl font-extrabold z-10 drop-shadow-md', trust.risk_level === 'low' ? 'text-brand-success' : trust.risk_level === 'medium' ? 'text-amber-400' : 'text-brand-alert')}>
            {trust.suspicious_count}
          </div>
          <div className="text-gray-400 text-sm font-medium z-10">Suspicious Reviews</div>
          <span className={clsx('text-xs px-3 py-1 rounded-full font-bold z-10 border', `badge-${trust.risk_level}`)}>
            {trust.risk_level.toUpperCase()} RISK
          </span>
        </div>
      </div>

      {/* AI Summary */}
      <div className="glass p-8 animate-slide-up" style={{ animationDelay: '0.2s' }}>
        <h2 className="text-xl font-bold mb-4 flex items-center gap-3 text-white">
          <div className="p-2 bg-gradient-to-br from-brand-cyan to-brand-lavender rounded-lg shadow-[0_0_10px_rgba(110,231,249,0.3)]">
            <span className="text-xl text-brand-navy">🤖</span>
          </div>
          AI Analysis Summary
        </h2>
        <p className="text-gray-300 leading-relaxed mb-8 text-lg">{ai_summary.summary}</p>
        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-brand-success/5 border border-brand-success/10 rounded-2xl p-5">
            <h3 className="font-bold text-brand-success flex items-center gap-2 mb-4 text-lg">
              <ThumbsUp className="w-5 h-5" /> Key Advantages
            </h3>
            <ul className="space-y-3 relative z-10">
              {ai_summary.pros?.map((p, i) => (
                <li key={i} className="flex gap-3 text-sm text-gray-200">
                  <span className="text-brand-success font-bold mt-0.5">✓</span> {p}
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-brand-alert/5 border border-brand-alert/10 rounded-2xl p-5">
            <h3 className="font-bold text-brand-alert flex items-center gap-2 mb-4 text-lg">
              <ThumbsDown className="w-5 h-5" /> Key Drawbacks
            </h3>
            <ul className="space-y-3 relative z-10">
              {ai_summary.cons?.map((c, i) => (
                <li key={i} className="flex gap-3 text-sm text-gray-200">
                  <span className="text-brand-alert font-bold mt-0.5">✗</span> {c}
                </li>
              ))}
            </ul>
          </div>
        </div>
        
        {ai_summary.recommendation_reason && (
          <div className="mt-6 p-5 bg-gradient-to-r from-brand-cyan/10 to-transparent border-l-4 border-brand-cyan rounded-r-xl text-sm text-gray-200">
            <span className="font-bold text-brand-cyan mr-2">💡 Recommendation Reason:</span>
            {ai_summary.recommendation_reason}
          </div>
        )}
        
        {ai_summary.best_for && (
          <div className="mt-6 grid md:grid-cols-2 gap-4 text-sm">
            <div className="p-4 bg-brand-success/10 border border-brand-success/20 rounded-xl">
              <span className="font-extrabold text-brand-success block mb-1">Target Audience:</span> 
              <span className="text-gray-300 leading-relaxed">{ai_summary.best_for}</span>
            </div>
            <div className="p-4 bg-brand-alert/10 border border-brand-alert/20 rounded-xl">
              <span className="font-extrabold text-brand-alert block mb-1">Avoid If You Note:</span> 
              <span className="text-gray-300 leading-relaxed">{ai_summary.avoid_if}</span>
            </div>
          </div>
        )}
      </div>

      {/* Sentiment %% */}
      <div className="grid md:grid-cols-3 gap-4 animate-slide-up" style={{ animationDelay: '0.3s' }}>
        {[
          { label: 'Positive', pct: sentiment.positive_pct, color: 'from-brand-success to-emerald-400', icon: ThumbsUp, textCol: 'text-brand-success' },
          { label: 'Neutral',  pct: sentiment.neutral_pct,  color: 'from-amber-400 to-yellow-500',      icon: null,       textCol: 'text-amber-400' },
          { label: 'Negative', pct: sentiment.negative_pct, color: 'from-brand-alert to-rose-400',      icon: ThumbsDown, textCol: 'text-brand-alert' },
        ].map(({ label, pct, color, icon: Icon, textCol }) => (
          <div key={label} className="glass p-5 border-t-2" style={{ borderTopColor: pct > 30 ? `var(--tw-colors-brand-${label === 'Positive' ? 'success' : label === 'Negative' ? 'alert' : 'amber'})` : 'transparent' }}>
            <div className="flex justify-between items-center mb-3">
              <span className="text-gray-400 text-sm font-medium uppercase tracking-wider">{label}</span>
              <span className={clsx("font-extrabold text-2xl", textCol)}>{pct?.toFixed(1)}%</span>
            </div>
            <div className="h-2.5 bg-brand-navy rounded-full overflow-hidden shadow-inner">
              <div className={clsx('h-full bg-gradient-to-r rounded-full transition-all duration-1000', color)} style={{ width: `${pct}%` }} />
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid md:grid-cols-2 gap-6 animate-slide-up" style={{ animationDelay: '0.4s' }}>
        {/* Distribution Bar Chart */}
        {distData.length > 0 && (
          <div className="glass p-6">
            <h2 className="text-lg font-bold text-white mb-6">Sentiment Distribution</h2>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={distData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ background: '#121826', border: '1px solid rgba(110,231,249,0.2)', borderRadius: 12, boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)' }} 
                  itemStyle={{ color: '#fff', fontWeight: 'bold' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={50}>
                  {distData.map((_, i) => <Cell key={i} fill={distColors[i]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Aspect Radar Chart */}
        {aspectData.length > 2 && (
          <div className="glass p-6">
            <h2 className="text-lg font-bold text-white mb-4">Feature Performance</h2>
            <ResponsiveContainer width="100%" height={240}>
              <RadarChart data={aspectData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
                <PolarGrid stroke="#ffffff" strokeOpacity={0.1} />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#6EE7F9', fontSize: 11, fontWeight: 'bold' }} />
                <Radar name="Score" dataKey="score" stroke="#6EE7F9" fill="#A78BFA" fillOpacity={0.3} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Individuals Reviews List */}
      <div className="glass overflow-hidden animate-slide-up" style={{ animationDelay: '0.5s' }}>
        <div className="p-6 md:p-8 border-b border-white/5 flex items-center justify-between">
          <h2 className="text-xl font-bold flex items-center gap-2 text-white">
            <MessageSquare className="w-5 h-5 text-brand-cyan" />
            Analyzed Reviews
          </h2>
          <span className="bg-brand-navy/80 text-brand-cyan text-xs font-bold px-3 py-1 rounded-lg border border-brand-cyan/20">
            {reviews.length} shown
          </span>
        </div>
        
        <div className="divide-y divide-white/5">
          {loadingReviews ? (
            <div className="p-12 text-center">
              <div className="w-8 h-8 border-4 border-brand-cyan/30 border-t-brand-cyan rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-400">Loading reviews...</p>
            </div>
          ) : reviews.length === 0 ? (
            <div className="p-12 text-center text-gray-500">No review details available.</div>
          ) : (
            reviews.map((rev) => {
              const isFake = rev.fake_probability > 0.5
              const isPositive = rev.sentiment_label === 'positive'
              const isNegative = rev.sentiment_label === 'negative'
              
              return (
                <div key={rev.id} className="p-6 md:p-8 hover:bg-white/5 transition-colors">
                  <div className="flex flex-col md:flex-row md:items-start gap-4 mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-gray-200">{rev.reviewer_name || 'Amazon Customer'}</span>
                        {rev.verified_purchase && (
                          <span className="text-[10px] uppercase font-bold text-brand-cyan bg-brand-cyan/10 px-2 py-0.5 rounded-full border border-brand-cyan/20 tracking-wider">Verified</span>
                        )}
                      </div>
                      
                      {rev.title && <h4 className="font-bold text-white text-lg mt-1">{rev.title}</h4>}
                    </div>
                    
                    <div className="flex flex-wrap gap-2 shrink-0">
                      {/* Fake/Real Tag */}
                      <div className={clsx(
                        "flex items-center gap-1.5 px-3 py-1 rounded-lg border text-sm font-bold shadow-sm",
                        isFake ? "bg-brand-alert/10 text-brand-alert border-brand-alert/30" : "bg-brand-success/10 text-brand-success border-brand-success/30"
                      )}>
                        {isFake ? <ShieldAlert className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
                        {isFake ? 'Suspicious' : 'Authentic'}
                        <span className="opacity-60 text-xs ml-1">({(rev.fake_probability * 100).toFixed(0)}%)</span>
                      </div>
                      
                      {/* Sentiment Tag */}
                      <div className={clsx(
                        "flex items-center gap-1.5 px-3 py-1 rounded-lg border text-sm font-bold shadow-sm",
                        isPositive ? "bg-brand-success/10 text-brand-success border-brand-success/30" : 
                        isNegative ? "bg-brand-alert/10 text-brand-alert border-brand-alert/30" : 
                        "bg-amber-500/10 text-amber-500 border-amber-500/30"
                      )}>
                        {isPositive ? <ThumbsUp className="w-4 h-4" /> : isNegative ? <ThumbsDown className="w-4 h-4" /> : null}
                        <span className="capitalize">{rev.sentiment_label}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 mb-3">
                    <div className="flex text-amber-400">
                      {[...Array(5)].map((_, i) => (
                        <Star key={i} className={clsx("w-4 h-4", i < (rev.rating || 0) ? "fill-amber-400" : "text-gray-600")} />
                      ))}
                    </div>
                    {rev.date && <span className="text-gray-500 text-sm ml-2">{rev.date}</span>}
                  </div>
                  
                  <p className={clsx("text-sm leading-relaxed", isFake ? "text-gray-500" : "text-gray-300")}>
                    {rev.text}
                  </p>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
