import { useState } from 'react'
import { usePlans, useCreateCheckout, useMySubscriptions, getApiErrorMessage } from '../hooks/useApi'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { Plan } from '../types'

function PlanCard({
  plan,
  hasActiveSub,
  onSubscribe,
  loading,
}: {
  plan: Plan
  hasActiveSub: boolean
  onSubscribe: (planId: number) => void
  loading: boolean
}) {
  const features: string[] = Array.isArray(plan.features)
    ? plan.features
    : plan.features
    ? JSON.parse(plan.features as unknown as string)
    : []

  return (
    <div className="card flex flex-col">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
        {plan.description && (
          <p className="text-gray-500 text-sm mt-1">{plan.description}</p>
        )}
      </div>

      <div className="mb-6">
        <span className="text-4xl font-bold text-gray-900">${plan.price}</span>
        <span className="text-gray-400 text-sm ml-1">
          / {plan.interval === 'monthly' ? 'месяц' : 'год'}
        </span>
      </div>

      {features.length > 0 && (
        <ul className="space-y-2 mb-6 flex-1">
          {features.map((feature, i) => (
            <li key={i} className="flex items-center gap-2 text-sm text-gray-600">
              <span className="text-green-500 font-bold">✓</span>
              {feature}
            </li>
          ))}
        </ul>
      )}

      <button
        onClick={() => onSubscribe(plan.id)}
        disabled={loading || hasActiveSub}
        className="btn-primary w-full mt-auto"
        title={hasActiveSub ? 'У вас уже есть активная подписка' : ''}
      >
        {loading ? 'Загрузка...' : hasActiveSub ? 'Уже есть подписка' : 'Оформить подписку'}
      </button>
    </div>
  )
}

export default function PlansPage() {
  const { data: plans, isLoading, error } = usePlans()
  const { data: subscriptions } = useMySubscriptions()
  const checkout = useCreateCheckout()
  const [checkoutError, setCheckoutError] = useState('')
  const [loadingPlanId, setLoadingPlanId] = useState<number | null>(null)

  const hasActiveSub = subscriptions?.some((s) => s.status === 'active') ?? false

  const handleSubscribe = async (planId: number) => {
    setCheckoutError('')
    setLoadingPlanId(planId)
    try {
      const result = await checkout.mutateAsync(planId)
      window.location.href = result.checkout_url
    } catch (err) {
      setCheckoutError(getApiErrorMessage(err))
    } finally {
      setLoadingPlanId(null)
    }
  }

  if (isLoading) return <LoadingSpinner />

  if (error) {
    return (
      <div className="text-center py-10 text-red-600">
        Ошибка загрузки тарифов
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Тарифные планы</h1>
        <p className="text-gray-500 mt-1">Выберите подходящий тариф</p>
      </div>

      {checkoutError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700 text-sm">
          {checkoutError}
        </div>
      )}

      {hasActiveSub && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-blue-700 text-sm">
          У вас уже есть активная подписка. Для смены тарифа сначала отмените текущую.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plans?.map((plan) => (
          <PlanCard
            key={plan.id}
            plan={plan}
            hasActiveSub={hasActiveSub}
            onSubscribe={handleSubscribe}
            loading={loadingPlanId === plan.id}
          />
        ))}
      </div>

      {plans?.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          Тарифные планы пока не добавлены
        </div>
      )}
    </div>
  )
}
