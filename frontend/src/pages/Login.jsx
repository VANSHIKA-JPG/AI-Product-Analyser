import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LogIn } from 'lucide-react'
import api from '../api/client'

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      const { data } = await api.post('/auth/login', form)
      localStorage.setItem('token', data.access_token)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center min-h-[70vh] animate-fade-in">
      <div className="glass p-8 w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-cyan to-brand-lavender flex items-center justify-center mx-auto mb-5 shadow-[0_0_20px_rgba(110,231,249,0.3)]">
            <LogIn className="w-7 h-7 text-brand-navy" />
          </div>
          <h1 className="text-2xl font-bold">Welcome back</h1>
          <p className="text-gray-400 text-sm mt-1">Sign in to your account</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Email</label>
            <input className="input" type="email" placeholder="you@example.com" required
              value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Password</label>
            <input className="input" type="password" placeholder="••••••••" required
              value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
        <p className="text-center text-sm text-gray-400 mt-6 pt-4 border-t border-white/5">
          Don't have an account? <Link to="/register" className="text-brand-cyan font-medium hover:text-brand-cyanHover hover:underline transition-colors">Register</Link>
        </p>
      </div>
    </div>
  )
}
