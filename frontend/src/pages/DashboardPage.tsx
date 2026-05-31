import { useAuthStore } from '../lib/authStore'
import { useMySubscriptions, useMyPayments, useMyInvoices } from '../hooks/useApi'
import StatusBadge from '../components/ui/StatusBadge'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { Link } from 'react-router-dom'

function StatCard({
  title,
  value,
  sub,
  icon,
}: {
  title: string
  value: string | number
  sub?: string
  icon: string
}) {
  return (
    <div className="card flex items-start gap-4">
      <div className="text-3xl">{icon}</div>
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const { data: subscriptions } = useMySubscriptions()
  const { data: payments } = useMyPayments()
  const { data: invoices } = useMyInvoices()

  const activeSub = subscriptions?.find((s) => s.status === 'active')
  const totalPaid = payments
    ?.filter((p) => p.status === 'succeeded')
    .reduce((sum, p) => sum + p.amount, 0) ?? 0

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Добро пожаловать, {user?.full_name || user?.email}
        </h1>
        <p className="text-gray-500 mt-1">Обзор вашего аккаунта</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon="🔄"
          title="Активная подписка"
          value={activeSub ? activeSub.plan?.name ?? '—' : 'Нет'}
          sub={
            activeSub?.current_period_end
              ? `до ${format(new Date(activeSub.current_period_end), 'dd MMM yyyy', { locale: ru })}`
              : undefined
          }
        />
        <StatCard
          icon="💳"
          title="Всего платежей"
          value={payments?.length ?? 0}
          sub="за всё время"
        />
        <StatCard
          icon="💰"
          title="Оплачено"
          value={`$${totalPaid.toFixed(2)}`}
          sub="успешные платежи"
        />
        <StatCard
          icon="📄"
          title="Инвойсов"
          value={invoices?.length ?? 0}
          sub="всего"
        />
      </div>

      {/* Active subscription detail */}
      {activeSub && (
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Текущая подписка</h2>
            <StatusBadge status={activeSub.status} />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Тариф</p>
              <p className="font-medium">{activeSub.plan?.name}</p>
            </div>
            <div>
              <p className="text-gray-500">Стоимость</p>
              <p className="font-medium">
                ${activeSub.plan?.price}/{activeSub.plan?.interval === 'monthly' ? 'мес' : 'год'}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Период начался</p>
              <p className="font-medium">
                {activeSub.current_period_start
                  ? format(new Date(activeSub.current_period_start), 'dd.MM.yyyy')
                  : '—'}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Следующее списание</p>
              <p className="font-medium">
                {activeSub.current_period_end
                  ? format(new Date(activeSub.current_period_end), 'dd.MM.yyyy')
                  : '—'}
              </p>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Link to="/dashboard/subscriptions" className="btn-secondary text-sm">
              Управление подпиской
            </Link>
          </div>
        </div>
      )}

      {/* No subscription CTA */}
      {!activeSub && (
        <div className="card border-2 border-dashed border-blue-200 text-center py-10 mb-6">
          <p className="text-gray-500 mb-4">У вас пока нет активной подписки</p>
          <Link to="/dashboard/plans" className="btn-primary">
            Выбрать тариф
          </Link>
        </div>
      )}

      {/* Recent payments */}
      {(payments?.length ?? 0) > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Последние платежи</h2>
            <Link to="/dashboard/payments" className="text-sm text-blue-600 hover:underline">
              Все платежи
            </Link>
          </div>
          <div className="space-y-3">
            {payments!.slice(0, 5).map((payment) => (
              <div
                key={payment.id}
                className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    ${payment.amount.toFixed(2)} {payment.currency.toUpperCase()}
                  </p>
                  <p className="text-xs text-gray-400">
                    {format(new Date(payment.created_at), 'dd MMM yyyy, HH:mm', { locale: ru })}
                  </p>
                </div>
                <StatusBadge status={payment.status} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
