import { useState } from 'react'
import { Plus, Trash2, GitCompare, Trophy, Star } from 'lucide-react'
import api from '../api/client'
import clsx from 'clsx'

export default function Compare() {
  const [urls, setUrls] = useState(['', ''])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const addUrl = () => setUrls(u => [...u, ''])
  const removeUrl = (i) => setUrls(u => u.filter((_, idx) => idx !== i))
  const updateUrl = (i, val) => setUrls(u => u.map((v, idx) => idx === i ? val : v))

  const handleCompare = async (e) => {
    e.preventDefault()
    const validUrls = urls.filter(u => u.trim())
    if (validUrls.length < 2) { setError('Enter at least 2 URLs'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const { data } = await api.post('/compare', { urls: validUrls })
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Comparison failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-in max-w-3xl mx-auto space-y-6">
      <div className="text-center py-8">
        <h1 className="text-3xl font-bold mb-2 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
          Compare Products
        </h1>
        <p className="text-gray-400">Add 2–5 Amazon product URLs to compare side by side</p>
      </div>

      <div className="glass p-6 space-y-4">
        {urls.map((url, i) => (
          <div key={i} className="flex gap-3">
            <input
              className="input flex-1"
              placeholder={`Product ${i + 1} URL — amazon.in/dp/...`}
              value={url}
              onChange={e => updateUrl(i, e.target.value)}
            />
            {urls.length > 2 && (
              <button onClick={() => removeUrl(i)} className="p-2.5 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all">
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
        <div className="flex gap-3">
          {urls.length < 5 && (
            <button onClick={addUrl} className="btn-secondary flex items-center gap-2 text-sm">
              <Plus className="w-4 h-4" /> Add URL
            </button>
          )}
          <button onClick={handleCompare} disabled={loading} className="btn-primary flex items-center gap-2 text-sm">
            {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <GitCompare className="w-4 h-4" />}
            {loading ? 'Comparing…' : 'Compare'}
          </button>
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
      </div>

      {result && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 animate-slide-up">
          {result.comparison.map((item) => (
            <div key={item.rank} className={clsx('glass p-6 relative', item.best_value && 'ring-2 ring-indigo-500')}>
              {item.best_value && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                  <Trophy className="w-3 h-3" /> Best Value
                </div>
              )}
              {item.image_url && <img src={item.image_url} alt={item.name} className="w-20 h-20 object-contain mx-auto mb-4 rounded-lg bg-gray-900 p-1" />}
              <p className="font-semibold text-sm text-center mb-3 line-clamp-2">{item.name}</p>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Price</span>
                  <span className="font-bold text-indigo-400">₹{item.price?.toLocaleString() ?? 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Rating</span>
                  <span className="flex items-center gap-1"><Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />{item.rating ?? 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Value Score</span>
                  <span className="font-bold text-emerald-400">{item.value_score}/100</span>
                </div>
                <div className="pt-2 border-t border-white/10 text-xs text-gray-500">{item.verdict}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
