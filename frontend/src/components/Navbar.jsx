import { Link, useLocation } from 'react-router-dom'
import { Search, BarChart2, History, GitCompare, LogIn, LogOut } from 'lucide-react'
import clsx from 'clsx'

const navLinks = [
  { to: '/',        label: 'Analyse',  icon: Search },
  { to: '/compare', label: 'Compare',  icon: GitCompare },
  { to: '/history', label: 'History',  icon: History },
]

export default function Navbar() {
  const { pathname } = useLocation()
  const token = localStorage.getItem('token')

  const handleLogout = () => {
    localStorage.removeItem('token')
    window.location.href = '/'
  }

  return (
    <nav className="sticky top-0 z-50 bg-gray-950/80 backdrop-blur-lg border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:shadow-indigo-500/40 transition-shadow">
              <BarChart2 className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              AI Analyser
            </span>
          </Link>

          {/* Nav Links */}
          <div className="flex items-center gap-1">
            {navLinks.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                  pathname === to
                    ? 'bg-indigo-500/20 text-indigo-400'
                    : 'text-gray-400 hover:text-gray-100 hover:bg-white/5'
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
                <Link to="/register" className="btn-primary text-sm">Register</Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
