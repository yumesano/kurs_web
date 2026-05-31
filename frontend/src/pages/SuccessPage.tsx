import { useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'

export default function SuccessPage() {
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id')
  const qc = useQueryClient()

  useEffect(() => {
    // Invalidate subscriptions so dashboard reflects the new subscription
    qc.invalidateQueries({ queryKey: ['subscriptions'] })
    qc.invalidateQueries({ queryKey: ['payments'] })
    qc.invalidateQueries({ queryKey: ['invoices'] })
  }, [qc])

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center max-w-md">
        <div className="text-6xl mb-6">🎉</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-3">
          Подписка оформлена!
        </h1>
        <p className="text-gray-500 mb-2">
          Оплата успешно прошла. Ваша подписка активирована.
        </p>
        {sessionId && (
          <p className="text-xs text-gray-400 font-mono mb-6">
            Session: {sessionId.slice(0, 20)}...
          </p>
        )}
        <div className="flex gap-3 justify-center">
          <Link to="/dashboard" className="btn-primary">
            На главную
          </Link>
          <Link to="/dashboard/subscriptions" className="btn-secondary">
            Мои подписки
          </Link>
        </div>
      </div>
    </div>
  )
}
