import { useMyPayments } from '../hooks/useApi'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import StatusBadge from '../components/ui/StatusBadge'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

export default function PaymentsPage() {
  const { data: payments, isLoading } = useMyPayments()

  if (isLoading) return <LoadingSpinner />

  const totalSucceeded =
    payments
      ?.filter((p) => p.status === 'succeeded')
      .reduce((sum, p) => sum + p.amount, 0) ?? 0

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">История платежей</h1>
        <p className="text-gray-500 mt-1">Все транзакции по вашему аккаунту</p>
      </div>

      {/* Summary */}
      {(payments?.length ?? 0) > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="card">
            <p className="text-sm text-gray-500">Всего транзакций</p>
            <p className="text-2xl font-bold">{payments?.length}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Успешных</p>
            <p className="text-2xl font-bold text-green-600">
              {payments?.filter((p) => p.status === 'succeeded').length}
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-500">Оплачено всего</p>
            <p className="text-2xl font-bold">${totalSucceeded.toFixed(2)}</p>
          </div>
        </div>
      )}

      {payments?.length === 0 ? (
        <div className="text-center py-16 text-gray-400">Платежей пока нет</div>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">ID</th>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">Сумма</th>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">Метод</th>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">Статус</th>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">Дата</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {payments?.map((payment) => (
                <tr key={payment.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-mono text-gray-400 text-xs">
                    #{payment.id}
                  </td>
                  <td className="px-6 py-4 font-semibold text-gray-900">
                    ${payment.amount.toFixed(2)}{' '}
                    <span className="text-gray-400 font-normal text-xs">
                      {payment.currency.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-600 capitalize">
                    {payment.payment_method || '—'}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={payment.status} />
                  </td>
                  <td className="px-6 py-4 text-gray-400">
                    {payment.paid_at
                      ? format(new Date(payment.paid_at), 'dd MMM yyyy, HH:mm', { locale: ru })
                      : format(new Date(payment.created_at), 'dd MMM yyyy, HH:mm', { locale: ru })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
