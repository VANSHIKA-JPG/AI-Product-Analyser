import { Link, useLocation } from 'react-router-dom'
import { Search, BarChart2, History, GitCompare, LogIn, LogOut, Info } from 'lucide-react'
import clsx from 'clsx'

const navLinks = [
  { to: '/',        label: 'Analyse',  icon: Search },
  { to: '/compare', label: 'Compare',  icon: GitCompare },
  { to: '/history', label: 'History',  icon: History },
  { to: '/about',   label: 'About',    icon: Info },
]

export default function Navbar() {
  const { pathname } = useLocation()
  const token = localStorage.getItem('token')

  const handleLogout = () => {
    localStorage.removeItem('token')
    window.location.href = '/'
  }

  const isAuthPage = pathname === '/login' || pathname === '/register'

  return (
    <nav className="sticky top-0 z-50 bg-brand-navy/80 backdrop-blur-xl border-b border-white/5 shadow-lg shadow-black/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-cyan to-brand-lavender flex items-center justify-center shadow-[0_0_15px_rgba(110,231,249,0.3)] group-hover:shadow-[0_0_25px_rgba(110,231,249,0.5)] transition-shadow duration-300">
              <BarChart2 className="w-5 h-5 text-brand-navy" />
            </div>
            <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-brand-cyan via-white to-brand-lavender bg-clip-text text-transparent group-hover:scale-[1.02] transition-transform">
              ReviewLens
            </span>
          </Link>

          {!isAuthPage && (
            <>
              {/* Nav Links */}
              <div className="flex items-center gap-1">
                {navLinks.map(({ to, label, icon: Icon }) => (
                  <Link
                    key={to}
                    to={to}
                    className={clsx(
                      'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300',
                      pathname === to
                        ? 'bg-brand-cyan/10 text-brand-cyan shadow-inner'
                        : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    {label}
                  </Link>
                ))}
              </div>

              {/* Auth */}
              <div className="flex items-center gap-2">
                {token ? (
                  <button onClick={handleLogout} className="btn-secondary flex items-center gap-2 text-sm">
                    <LogOut className="w-4 h-4" /> Logout
                  </button>
                ) : (
                  <>
                    <Link to="/login" className="btn-secondary text-sm flex items-center gap-2">
                      <LogIn className="w-4 h-4" /> Login
                    </Link>
                    <Link to="/register" className="btn-primary text-sm flex items-center gap-2 py-2">Get Started</Link>
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
