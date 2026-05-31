import { useMyInvoices } from '../hooks/useApi'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import StatusBadge from '../components/ui/StatusBadge'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

export default function InvoicesPage() {
  const { data: invoices, isLoading } = useMyInvoices()

  if (isLoading) return <LoadingSpinner />

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Инвойсы</h1>
        <p className="text-gray-500 mt-1">Все счета на оплату</p>
      </div>

      {invoices?.length === 0 ? (
        <div className="text-center py-16 text-gray-400">Инвойсов пока нет</div>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">ID</th>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">Период</th>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">Сумма</th>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">Статус</th>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">Создан</th>
                <th className="text-left px-6 py-3 text-gray-500 font-medium">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {invoices?.map((invoice) => (
                <tr key={invoice.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-mono text-gray-400 text-xs">
                    #{invoice.id}
                  </td>
                  <td className="px-6 py-4 text-gray-600">
                    {invoice.period_start && invoice.period_end ? (
                      <>
                        {format(new Date(invoice.period_start), 'dd.MM.yyyy')}
                        {' — '}
                        {format(new Date(invoice.period_end), 'dd.MM.yyyy')}
                      </>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-6 py-4 font-semibold text-gray-900">
                    ${invoice.amount_due.toFixed(2)}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={invoice.status} />
                  </td>
                  <td className="px-6 py-4 text-gray-400">
                    {format(new Date(invoice.created_at), 'dd MMM yyyy', { locale: ru })}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      {invoice.hosted_invoice_url && (
                        <a
                          href={invoice.hosted_invoice_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline text-xs"
                        >
                          Открыть
                        </a>
                      )}
                      {invoice.invoice_pdf && (
                        <a
                          href={invoice.invoice_pdf}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline text-xs"
                        >
                          PDF
                        </a>
                      )}
                    </div>
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
