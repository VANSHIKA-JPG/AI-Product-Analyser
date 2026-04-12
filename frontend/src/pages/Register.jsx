import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { UserPlus, ShieldCheck, TrendingUp, Sparkles, CheckCircle2, XCircle, BarChart2 } from 'lucide-react'
import clsx from 'clsx'
import api from '../api/client'

export default function Register() {
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  // Live password validation
  const validations = {
    length: form.password.length >= 8,
    number: /\d/.test(form.password),
    special: /[^A-Za-z0-9]/.test(form.password),
  }
  const strength = Object.values(validations).filter(Boolean).length
  const strengthText = strength === 0 ? '' : strength === 1 ? 'Weak' : strength === 2 ? 'Fair' : 'Strong'
  const strengthColor = strength === 0 ? 'bg-gray-700' : strength === 1 ? 'bg-brand-alert' : strength === 2 ? 'bg-amber-400' : 'bg-brand-success'

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (strength < 3) {
      setError('Please meet all password requirements')
      return
    }
    setLoading(true); setError('')
    try {
      const { data } = await api.post('/auth/register', form)
      localStorage.setItem('token', data.access_token)
      navigate('/')
    } catch (err) {
      const d = err.response?.data?.detail;
      if (Array.isArray(d)) {
        setError(d.map(e => e.msg).join(' • '));
      } else {
        setError(d || 'Registration failed');
      }
    } finally {
      setLoading(false)
    }
  }

  const ValidationItem = ({ label, isValid }) => (
    <div className={clsx("flex items-center gap-2 text-xs", isValid ? "text-brand-success" : "text-gray-500")}>
      {isValid ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
      {label}
    </div>
  )

  return (
    <div className="flex items-center justify-center min-h-[85vh] animate-fade-in p-4">
      {/* Main Container - Split Screen Glass Card */}
      <div className="w-full max-w-5xl flex flex-col lg:flex-row bg-brand-glass/40 backdrop-blur-2xl rounded-3xl overflow-hidden border border-white/10 shadow-[0_0_40px_rgba(110,231,249,0.05)] shadow-black/50">
        
        {/* Left Side: Product Context & Social Proof */}
        <div className="lg:w-5/12 relative p-10 flex flex-col justify-between overflow-hidden bg-brand-navy border-r border-white/5">
          {/* Subtle grid pattern background */}
          <div className="absolute inset-0 opacity-[0.03] bg-[linear-gradient(to_right,#fff_1px,transparent_1px),linear-gradient(to_bottom,#fff_1px,transparent_1px)] bg-[size:24px_24px]"></div>
          {/* Blur orbs */}
          <div className="absolute -top-32 -left-32 w-96 h-96 bg-brand-cyan/20 blur-[100px] rounded-full pointer-events-none"></div>
          <div className="absolute -bottom-32 -right-32 w-96 h-96 bg-brand-lavender/20 blur-[100px] rounded-full pointer-events-none"></div>

          <div className="relative z-10 space-y-8">
            <Link to="/" className="flex items-center gap-3 w-fit group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-cyan to-brand-lavender flex items-center justify-center shadow-[0_0_15px_rgba(110,231,249,0.3)]">
                <BarChart2 className="w-6 h-6 text-brand-navy" />
              </div>
              <span className="font-extrabold text-2xl tracking-tight text-white group-hover:text-brand-cyan transition-colors">
                ReviewLens
              </span>
            </Link>

            <div className="space-y-6 pt-8">
              <h2 className="text-3xl font-extrabold text-white leading-tight">
                Unlock the Truth <br/> Behind Every Review.
              </h2>
              <p className="text-gray-400">Join thousands of smart shoppers using AI to cut through e-commerce noise.</p>
              
              <div className="space-y-5 pt-4">
                <div className="flex items-start gap-4">
                  <div className="bg-brand-cyan/10 p-2.5 rounded-xl border border-brand-cyan/20 mt-1">
                    <ShieldCheck className="w-5 h-5 text-brand-cyan" />
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-200">Fake Review Detection</h4>
                    <p className="text-sm text-gray-500 mt-1">Machine learning stops manipulated reviews in their tracks.</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="bg-brand-lavender/10 p-2.5 rounded-xl border border-brand-lavender/20 mt-1">
                    <TrendingUp className="w-5 h-5 text-brand-lavender" />
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-200">Sentiment Analysis</h4>
                    <p className="text-sm text-gray-500 mt-1">Dual-engine models reveal true customer satisfaction.</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="bg-brand-success/10 p-2.5 rounded-xl border border-brand-success/20 mt-1">
                    <Sparkles className="w-5 h-5 text-brand-success" />
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-200">AI Purchasing Summaries</h4>
                    <p className="text-sm text-gray-500 mt-1">Instant pros, cons, and bottom-line recommendations.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="relative z-10 pt-12 mt-auto">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">Trusted By Shoppers From</p>
            <div className="flex gap-6 opacity-40 grayscale">
              {/* Mock logos text */}
              <div className="font-bold text-lg">Amazon</div>
              <div className="font-bold text-lg">Flipkart</div>
              <div className="font-bold text-lg">Etsy</div>
            </div>
          </div>
        </div>

        {/* Right Side: Signup Form */}
        <div className="lg:w-7/12 p-8 md:p-12 lg:px-16 flex flex-col justify-center relative">
          <div className="max-w-md mx-auto w-full">
            <div className="mb-8">
              <h3 className="text-2xl font-bold text-white">Create an account</h3>
              <p className="text-gray-400 text-sm mt-2">Sign up to save your analyses and view history.</p>
            </div>

            {/* Social Auth */}
            <div className="grid grid-cols-2 gap-3 mb-6">
              <button type="button" className="flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white text-sm font-medium py-2.5 rounded-xl transition-all">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Google
              </button>
              <button type="button" className="flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white text-sm font-medium py-2.5 rounded-xl transition-all">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                </svg>
                GitHub
              </button>
            </div>

            <div className="relative mb-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/10"></div>
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-brand-glass px-3 text-gray-500 uppercase">Or register with email</span>
              </div>
            </div>

            {/* Manual Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Username</label>
                <input className="input" type="text" placeholder="johndoe" required
                  value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Email address</label>
                <input className="input" type="email" placeholder="you@example.com" required
                  value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
              </div>
              <div>
                <div className="flex justify-between mb-1.5">
                  <label className="block text-sm font-medium text-gray-300">Password</label>
                  {form.password && (
                    <span className={clsx("text-xs font-semibold uppercase", 
                      strength === 3 ? "text-brand-success" : strength === 2 ? "text-amber-400" : "text-brand-alert")}>
                      {strengthText}
                    </span>
                  )}
                </div>
                <input className="input" type="password" placeholder="••••••••" required
                  value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
                
                {/* Password strength meter & live validation */}
                <div className="mt-3">
                  <div className="flex gap-1 mb-2 h-1.5">
                    {[1, 2, 3].map((level) => (
                      <div key={level} className={clsx(
                        "flex-1 rounded-full transition-colors duration-300",
                        form.password.length === 0 ? "bg-gray-800" : level <= strength ? strengthColor : "bg-gray-800"
                      )}></div>
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-3">
                    <ValidationItem label="At least 8 characters" isValid={validations.length} />
                    <ValidationItem label="Contains a number" isValid={validations.number} />
                    <ValidationItem label="Contains special char" isValid={validations.special} />
                  </div>
                </div>
              </div>
              
              {error && <p className="text-brand-alert text-sm font-medium bg-brand-alert/10 border border-brand-alert/20 p-3 rounded-lg flex items-center gap-2"><XCircle className="w-4 h-4 shrink-0" /> {error}</p>}
              
              <button 
                type="submit" 
                className="btn-primary w-full flex items-center justify-center gap-2 mt-2" 
                disabled={loading || (form.password && strength < 3)}
              >
                {loading ? 'Creating account…' : <>Create Account <UserPlus className="w-4 h-4 ml-1" /></>}
              </button>
            </form>

            <div className="mt-8 text-center text-sm text-gray-400">
              By registering, you agree to our <a href="#" className="text-brand-cyan hover:underline">Terms of Service</a> and <a href="#" className="text-brand-cyan hover:underline">Privacy Policy</a>.
            </div>
            
            <p className="text-center text-sm text-gray-400 mt-6 pt-4 border-t border-white/5">
               Already have an account? <Link to="/login" className="text-brand-cyan font-bold hover:text-brand-cyanHover hover:underline transition-colors ml-1">Log in</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
