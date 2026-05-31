import clsx from 'clsx'

const statusConfig: Record<string, { label: string; className: string }> = {
  active: { label: 'Активна', className: 'bg-green-100 text-green-800' },
  canceled: { label: 'Отменена', className: 'bg-red-100 text-red-800' },
  past_due: { label: 'Просрочена', className: 'bg-yellow-100 text-yellow-800' },
  trialing: { label: 'Пробный период', className: 'bg-blue-100 text-blue-800' },
  unpaid: { label: 'Не оплачена', className: 'bg-orange-100 text-orange-800' },
  incomplete: { label: 'Не завершена', className: 'bg-gray-100 text-gray-600' },
  paused: { label: 'Приостановлена', className: 'bg-purple-100 text-purple-800' },
  paid: { label: 'Оплачен', className: 'bg-green-100 text-green-800' },
  open: { label: 'Открыт', className: 'bg-blue-100 text-blue-800' },
  draft: { label: 'Черновик', className: 'bg-gray-100 text-gray-600' },
  void: { label: 'Аннулирован', className: 'bg-red-100 text-red-800' },
  succeeded: { label: 'Выполнен', className: 'bg-green-100 text-green-800' },
  pending: { label: 'В обработке', className: 'bg-yellow-100 text-yellow-800' },
  failed: { label: 'Ошибка', className: 'bg-red-100 text-red-800' },
  refunded: { label: 'Возврат', className: 'bg-purple-100 text-purple-800' },
}

export default function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status] ?? { label: status, className: 'bg-gray-100 text-gray-600' }
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        config.className,
      )}
    >
      {config.label}
    </span>
  )
}
