import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../lib/authStore'
import clsx from 'clsx'

const navItems = [
  { path: '/dashboard', label: 'Главная', icon: '🏠', exact: true },
  { path: '/dashboard/plans', label: 'Тарифы', icon: '📋' },
  { path: '/dashboard/subscriptions', label: 'Подписки', icon: '🔄' },
  { path: '/dashboard/invoices', label: 'Инвойсы', icon: '📄' },
  { path: '/dashboard/payments', label: 'Платежи', icon: '💳' },
]

const adminItems = [
  { path: '/dashboard/admin', label: 'Администрирование', icon: '⚙️' },
]

export default function DashboardLayout() {
  const { user, logout } = useAuthStore()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const isActive = (path: string, exact = false) => {
    if (exact) return location.pathname === path
    return location.pathname.startsWith(path) && !(exact && location.pathname !== path)
  }

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-xl font-bold text-blue-600">SubscriptionAPI</h1>
          <p className="text-xs text-gray-400 mt-1">Управление подписками</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive(item.path, item.exact)
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
              )}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          ))}

          {user?.role === 'admin' && (
            <>
              <div className="pt-4 pb-1">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3">
                  Администратор
                </p>
              </div>
              {adminItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={clsx(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive(item.path)
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                  )}
                >
                  <span>{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </>
          )}
        </nav>

        {/* User info */}
        <div className="p-4 border-t border-gray-100">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold text-sm">
              {user?.email?.[0]?.toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user?.full_name || user?.email}
              </p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full text-left text-sm text-gray-500 hover:text-red-600 transition-colors px-3 py-1.5 rounded hover:bg-red-50"
          >
            Выйти
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
