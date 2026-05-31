import { useState } from 'react'
import {
  useAllUsers,
  useAllSubscriptions,
  useAllInvoices,
  useAllPayments,
  useCreatePlan,
  usePlans,
  getApiErrorMessage,
} from '../hooks/useApi'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import StatusBadge from '../components/ui/StatusBadge'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { Plan, User } from '../types'

type Tab = 'users' | 'subscriptions' | 'invoices' | 'payments' | 'plans'

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>('users')

  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: 'users', label: 'Пользователи', icon: '👥' },
    { key: 'subscriptions', label: 'Подписки', icon: '🔄' },
    { key: 'invoices', label: 'Инвойсы', icon: '📄' },
    { key: 'payments', label: 'Платежи', icon: '💳' },
    { key: 'plans', label: 'Тарифы', icon: '📋' },
  ]

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Панель администратора</h1>
        <p className="text-gray-500 mt-1">Управление системой</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-xl w-fit">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {tab === 'users' && <UsersTab />}
      {tab === 'subscriptions' && <SubscriptionsTab />}
      {tab === 'invoices' && <InvoicesTab />}
      {tab === 'payments' && <PaymentsTab />}
      {tab === 'plans' && <PlansTab />}
    </div>
  )
}

function UsersTab() {
  const { data: users, isLoading } = useAllUsers()
  if (isLoading) return <LoadingSpinner />
  return (
    <div className="card overflow-hidden p-0">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-100">
          <tr>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">ID</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Email</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Имя</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Роль</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Статус</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Регистрация</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {users?.map((user: User) => (
            <tr key={user.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 text-gray-400">#{user.id}</td>
              <td className="px-6 py-4 text-gray-900">{user.email}</td>
              <td className="px-6 py-4 text-gray-600">{user.full_name || '—'}</td>
              <td className="px-6 py-4">
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  user.role === 'admin'
                    ? 'bg-purple-100 text-purple-700'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {user.role === 'admin' ? 'Администратор' : 'Пользователь'}
                </span>
              </td>
              <td className="px-6 py-4">
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {user.is_active ? 'Активен' : 'Заблокирован'}
                </span>
              </td>
              <td className="px-6 py-4 text-gray-400 text-xs">
                {format(new Date(user.created_at), 'dd MMM yyyy', { locale: ru })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-100 text-xs text-gray-400">
        Всего пользователей: {users?.length ?? 0}
      </div>
    </div>
  )
}

function SubscriptionsTab() {
  const { data: subscriptions, isLoading } = useAllSubscriptions()
  if (isLoading) return <LoadingSpinner />
  return (
    <div className="card overflow-hidden p-0">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-100">
          <tr>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">ID</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Пользователь</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Тариф</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Статус</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Конец периода</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {subscriptions?.map((sub) => (
            <tr key={sub.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 text-gray-400">#{sub.id}</td>
              <td className="px-6 py-4">ID: {sub.user_id}</td>
              <td className="px-6 py-4">{sub.plan?.name ?? `ID: ${sub.plan_id}`}</td>
              <td className="px-6 py-4"><StatusBadge status={sub.status} /></td>
              <td className="px-6 py-4 text-gray-400">
                {sub.current_period_end
                  ? format(new Date(sub.current_period_end), 'dd.MM.yyyy')
                  : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function InvoicesTab() {
  const { data: invoices, isLoading } = useAllInvoices()
  if (isLoading) return <LoadingSpinner />
  return (
    <div className="card overflow-hidden p-0">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-100">
          <tr>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">ID</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Пользователь</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Сумма</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Статус</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Дата</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {invoices?.map((inv) => (
            <tr key={inv.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 text-gray-400">#{inv.id}</td>
              <td className="px-6 py-4">ID: {inv.user_id}</td>
              <td className="px-6 py-4 font-semibold">${inv.amount_due.toFixed(2)}</td>
              <td className="px-6 py-4"><StatusBadge status={inv.status} /></td>
              <td className="px-6 py-4 text-gray-400 text-xs">
                {format(new Date(inv.created_at), 'dd MMM yyyy', { locale: ru })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PaymentsTab() {
  const { data: payments, isLoading } = useAllPayments()
  if (isLoading) return <LoadingSpinner />
  return (
    <div className="card overflow-hidden p-0">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-100">
          <tr>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">ID</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Пользователь</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Сумма</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Статус</th>
            <th className="text-left px-6 py-3 text-gray-500 font-medium">Дата</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {payments?.map((p) => (
            <tr key={p.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 text-gray-400">#{p.id}</td>
              <td className="px-6 py-4">ID: {p.user_id}</td>
              <td className="px-6 py-4 font-semibold">${p.amount.toFixed(2)}</td>
              <td className="px-6 py-4"><StatusBadge status={p.status} /></td>
              <td className="px-6 py-4 text-gray-400 text-xs">
                {format(new Date(p.created_at), 'dd MMM yyyy', { locale: ru })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PlansTab() {
  const { data: plans, isLoading } = usePlans()
  const createPlan = useCreatePlan()
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    currency: 'usd',
    interval: 'monthly' as 'monthly' | 'yearly',
    features: '',
  })
  const [error, setError] = useState('')

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      const features = formData.features
        ? formData.features.split('\n').filter(Boolean)
        : undefined
      await createPlan.mutateAsync({
        name: formData.name,
        description: formData.description || undefined,
        price: parseFloat(formData.price),
        currency: formData.currency,
        interval: formData.interval,
        features,
      } as Partial<Plan>)
      setShowForm(false)
      setFormData({ name: '', description: '', price: '', currency: 'usd', interval: 'monthly', features: '' })
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  if (isLoading) return <LoadingSpinner />

  return (
    <div>
      <div className="flex justify-end mb-4">
        <button onClick={() => setShowForm(!showForm)} className="btn-primary text-sm">
          {showForm ? 'Отмена' : '+ Добавить тариф'}
        </button>
      </div>

      {showForm && (
        <div className="card mb-6">
          <h3 className="font-semibold text-gray-900 mb-4">Новый тарифный план</h3>
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Название</label>
                <input
                  className="input-field"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Цена (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  className="input-field"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Описание</label>
              <input
                className="input-field"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Период</label>
              <select
                className="input-field"
                value={formData.interval}
                onChange={(e) => setFormData({ ...formData, interval: e.target.value as 'monthly' | 'yearly' })}
              >
                <option value="monthly">Ежемесячно</option>
                <option value="yearly">Ежегодно</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Возможности (каждая с новой строки)
              </label>
              <textarea
                className="input-field"
                rows={4}
                value={formData.features}
                onChange={(e) => setFormData({ ...formData, features: e.target.value })}
                placeholder={"До 5 проектов\n1 ГБ хранилища\nEmail поддержка"}
              />
            </div>
            {error && <p className="text-red-600 text-sm">{error}</p>}
            <button type="submit" disabled={createPlan.isPending} className="btn-primary">
              {createPlan.isPending ? 'Создание...' : 'Создать тариф'}
            </button>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {plans?.map((plan) => (
          <div key={plan.id} className="card">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-900">{plan.name}</h3>
              <span className={`text-xs px-2 py-0.5 rounded-full ${plan.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                {plan.is_active ? 'Активен' : 'Отключён'}
              </span>
            </div>
            <p className="text-xl font-bold text-gray-900 mb-1">
              ${plan.price}
              <span className="text-sm font-normal text-gray-400 ml-1">
                / {plan.interval === 'monthly' ? 'мес' : 'год'}
              </span>
            </p>
            {plan.description && <p className="text-sm text-gray-500">{plan.description}</p>}
          </div>
        ))}
      </div>
    </div>
  )
}
