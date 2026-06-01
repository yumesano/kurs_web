import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useSyncCheckout, useMySubscriptions } from '../hooks/useApi'
import { Subscription } from '../types'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

// Fallback polling — kicks in only if the direct sync also fails
const MAX_POLL_ATTEMPTS = 10   // 10 × 2 с = 20 секунд
const POLL_INTERVAL     = 2000

type Phase = 'syncing' | 'polling' | 'done' | 'timeout'

function Spinner() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <div className="inline-block w-14 h-14 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6" />
        <p className="text-gray-600 text-lg font-medium">Подтверждаем оплату…</p>
        <p className="text-gray-400 text-sm mt-2">
          Обрабатываем уведомление от Stripe, подождите несколько секунд
        </p>
      </div>
    </div>
  )
}

export default function SuccessPage() {
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id')

  const syncCheckout  = useSyncCheckout()
  const syncCalledRef = useRef(false)   // prevent double-call in React Strict Mode

  const [activeSub, setActiveSub] = useState<Subscription | null>(null)
  const [phase, setPhase]         = useState<Phase>('syncing')
  const [attempts, setAttempts]   = useState(0)

  const { data: subscriptions, refetch } = useMySubscriptions()

  // ── Safety net: if syncing phase lasts more than 10 s, force polling ──
  // Covers the case when StrictMode double-invoke skips the mutation call
  // or the backend itself hangs beyond the 8-second asyncio timeout.
  useEffect(() => {
    if (phase !== 'syncing') return
    const id = setTimeout(() => setPhase('polling'), 10000)
    return () => clearTimeout(id)
  }, [phase])

  // ── Phase 1: direct sync via session_id ───────────────────────────────
  // This works even without webhooks: we call Stripe directly to get the
  // checkout session, verify payment_status === "paid", then activate the
  // local subscription. Fast path: resolves in ~1 second.
  useEffect(() => {
    if (syncCalledRef.current) return
    syncCalledRef.current = true

    if (!sessionId) {
      // No session_id in URL — skip sync, go to polling fallback
      setPhase('polling')
      return
    }

    syncCheckout.mutate(sessionId, {
      onSuccess: (sub) => {
        setActiveSub(sub)
        setPhase('done')
      },
      onError: () => {
        // Sync failed (payment pending / Stripe key not configured)
        // — fall back to webhook-based polling
        setPhase('polling')
      },
    })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps — intentionally run once

  // ── Phase 2: fallback polling (webhook-based path) ────────────────────
  // Runs only when Phase 1 fails. Checks every 2 s whether the webhook
  // has updated the subscription status to active/trialing.
  useEffect(() => {
    if (phase !== 'polling') return

    const found = subscriptions?.find(
      (s) => s.status === 'active' || s.status === 'trialing'
    )
    if (found) {
      setActiveSub(found)
      setPhase('done')
      return
    }

    if (attempts >= MAX_POLL_ATTEMPTS) {
      setPhase('timeout')
      return
    }

    const timer = setTimeout(() => {
      setAttempts((a) => a + 1) // useState → triggers re-render → effect re-runs
      refetch()
    }, POLL_INTERVAL)

    return () => clearTimeout(timer)
  }, [subscriptions, phase, refetch, attempts])

  // ── Loading states ─────────────────────────────────────────────────────
  if (phase === 'syncing' || phase === 'polling') return <Spinner />

  // ── Success / Timeout screen ───────────────────────────────────────────
  return (
    <div className="flex items-center justify-center min-h-[60vh] px-4">
      <div className="w-full max-w-lg">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-6">
            <svg
              className="w-10 h-10 text-green-600"
              fill="none" viewBox="0 0 24 24"
              stroke="currentColor" strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Оплата прошла успешно!
          </h1>
          <p className="text-gray-500">
            {phase === 'timeout'
              ? 'Платёж принят. Подписка активируется в течение нескольких секунд.'
              : 'Ваша подписка активирована. Добро пожаловать!'}
          </p>
        </div>

        {/* Subscription details card */}
        {activeSub ? (
          <div className="card mb-6">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
              Детали подписки
            </h2>
            <div className="space-y-0">

              <div className="flex items-center justify-between py-3 border-b border-gray-100">
                <span className="text-gray-500 text-sm">Тарифный план</span>
                <span className="font-semibold text-gray-900">
                  {activeSub.plan?.name ?? `#${activeSub.id}`}
                </span>
              </div>

              <div className="flex items-center justify-between py-3 border-b border-gray-100">
                <span className="text-gray-500 text-sm">Стоимость</span>
                <span className="font-semibold text-gray-900">
                  ${activeSub.plan?.price}
                  <span className="text-gray-400 font-normal text-sm ml-1">
                    / {activeSub.plan?.interval === 'monthly' ? 'месяц' : 'год'}
                  </span>
                </span>
              </div>

              <div className="flex items-center justify-between py-3 border-b border-gray-100">
                <span className="text-gray-500 text-sm">Статус</span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                  {activeSub.status === 'active' ? 'Активна' : 'Пробный период'}
                </span>
              </div>

              {activeSub.current_period_start && (
                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <span className="text-gray-500 text-sm">Начало периода</span>
                  <span className="font-medium text-gray-900">
                    {format(new Date(activeSub.current_period_start), 'dd MMMM yyyy', { locale: ru })}
                  </span>
                </div>
              )}

              {activeSub.current_period_end && (
                <div className="flex items-center justify-between py-3">
                  <span className="text-gray-500 text-sm">Следующее списание</span>
                  <span className="font-medium text-gray-900">
                    {format(new Date(activeSub.current_period_end), 'dd MMMM yyyy', { locale: ru })}
                  </span>
                </div>
              )}

            </div>
          </div>
        ) : (
          /* Timeout: no subscription details available */
          <div className="card mb-6 bg-yellow-50 border-yellow-200">
            <div className="flex gap-3">
              <svg
                className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5"
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-yellow-800">
                Платёж принят, но подтверждение ещё обрабатывается. Обновите страницу
                через несколько секунд — подписка появится в разделе «Мои подписки».
              </p>
            </div>
          </div>
        )}

        {/* Session ID */}
        {sessionId && (
          <div className="bg-gray-50 rounded-lg p-3 mb-6">
            <p className="text-xs text-gray-400 font-mono break-all">
              <span className="text-gray-500 font-sans not-italic">Session ID: </span>
              {sessionId}
            </p>
          </div>
        )}

        {/* Navigation */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link to="/dashboard" className="btn-primary text-center">
            На главную
          </Link>
          <Link to="/dashboard/subscriptions" className="btn-secondary text-center">
            Мои подписки
          </Link>
          <Link to="/dashboard/invoices" className="btn-secondary text-center">
            Инвойсы
          </Link>
        </div>

      </div>
    </div>
  )
}
