import { useState } from 'react'
import { useMySubscriptions, useCancelSubscription, getApiErrorMessage } from '../hooks/useApi'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import StatusBadge from '../components/ui/StatusBadge'
import { Subscription } from '../types'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { Link } from 'react-router-dom'

function SubscriptionCard({
  sub,
  onCancel,
  canceling,
}: {
  sub: Subscription
  onCancel: (id: number) => void
  canceling: boolean
}) {
  return (
    <div className="card">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {sub.plan?.name ?? `Подписка #${sub.id}`}
          </h3>
          {sub.plan && (
            <p className="text-gray-500 text-sm mt-0.5">
              ${sub.plan.price} / {sub.plan.interval === 'monthly' ? 'месяц' : 'год'}
            </p>
          )}
        </div>
        <StatusBadge status={sub.status} />
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm mb-4">
        <div>
          <p className="text-gray-400">Начало периода</p>
          <p className="font-medium">
            {sub.current_period_start
              ? format(new Date(sub.current_period_start), 'dd MMM yyyy', { locale: ru })
              : '—'}
          </p>
        </div>
        <div>
          <p className="text-gray-400">Конец периода</p>
          <p className="font-medium">
            {sub.current_period_end
              ? format(new Date(sub.current_period_end), 'dd MMM yyyy', { locale: ru })
              : '—'}
          </p>
        </div>
        {sub.canceled_at && (
          <div>
            <p className="text-gray-400">Дата отмены</p>
            <p className="font-medium text-red-600">
              {format(new Date(sub.canceled_at), 'dd MMM yyyy', { locale: ru })}
            </p>
          </div>
        )}
        <div>
          <p className="text-gray-400">ID в Stripe</p>
          <p className="font-mono text-xs text-gray-500 truncate">
            {sub.stripe_subscription_id ?? '—'}
          </p>
        </div>
      </div>

      {sub.status === 'active' && (
        <button
          onClick={() => onCancel(sub.id)}
          disabled={canceling}
          className="btn-danger text-sm"
        >
          {canceling ? 'Отмена...' : 'Отменить подписку'}
        </button>
      )}
    </div>
  )
}

export default function SubscriptionsPage() {
  const { data: subscriptions, isLoading } = useMySubscriptions()
  const cancel = useCancelSubscription()
  const [error, setError] = useState('')
  const [cancelingId, setCancelingId] = useState<number | null>(null)
  const [successMsg, setSuccessMsg] = useState('')

  const handleCancel = async (id: number) => {
    if (!confirm('Вы уверены, что хотите отменить подписку?')) return
    setError('')
    setSuccessMsg('')
    setCancelingId(id)
    try {
      await cancel.mutateAsync(id)
      setSuccessMsg('Подписка будет отменена в конце текущего периода')
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setCancelingId(null)
    }
  }

  if (isLoading) return <LoadingSpinner />

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Мои подписки</h1>
          <p className="text-gray-500 mt-1">История и управление подписками</p>
        </div>
        <Link to="/dashboard/plans" className="btn-primary text-sm">
          + Новая подписка
        </Link>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 text-red-700 text-sm">
          {error}
        </div>
      )}
      {successMsg && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4 text-green-700 text-sm">
          {successMsg}
        </div>
      )}

      <div className="space-y-4">
        {subscriptions?.map((sub) => (
          <SubscriptionCard
            key={sub.id}
            sub={sub}
            onCancel={handleCancel}
            canceling={cancelingId === sub.id}
          />
        ))}
      </div>

      {subscriptions?.length === 0 && (
        <div className="text-center py-16">
          <p className="text-gray-400 mb-4">У вас пока нет подписок</p>
          <Link to="/dashboard/plans" className="btn-primary">
            Выбрать тариф
          </Link>
        </div>
      )}
    </div>
  )
}
