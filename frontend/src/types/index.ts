export interface User {
  id: number
  email: string
  full_name: string | null
  role: 'admin' | 'user'
  is_active: boolean
  stripe_customer_id: string | null
  created_at: string
  updated_at: string
}

export interface Plan {
  id: number
  name: string
  description: string | null
  price: number
  currency: string
  interval: 'monthly' | 'yearly'
  features: string[] | null
  stripe_price_id: string | null
  stripe_product_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Subscription {
  id: number
  user_id: number
  plan_id: number
  status: SubscriptionStatus
  stripe_subscription_id: string | null
  stripe_customer_id: string | null
  current_period_start: string | null
  current_period_end: string | null
  canceled_at: string | null
  trial_end: string | null
  created_at: string
  updated_at: string
  plan: Plan | null
}

export type SubscriptionStatus =
  | 'active'
  | 'canceled'
  | 'past_due'
  | 'trialing'
  | 'unpaid'
  | 'incomplete'
  | 'paused'

export interface Invoice {
  id: number
  user_id: number
  subscription_id: number | null
  stripe_invoice_id: string | null
  amount_due: number
  amount_paid: number
  currency: string
  status: 'draft' | 'open' | 'paid' | 'uncollectible' | 'void'
  hosted_invoice_url: string | null
  invoice_pdf: string | null
  period_start: string | null
  period_end: string | null
  due_date: string | null
  paid_at: string | null
  created_at: string
  updated_at: string
}

export interface Payment {
  id: number
  user_id: number
  invoice_id: number | null
  stripe_payment_intent_id: string | null
  amount: number
  currency: string
  status: 'pending' | 'succeeded' | 'failed' | 'refunded' | 'canceled'
  payment_method: string | null
  failure_message: string | null
  paid_at: string | null
  created_at: string
  updated_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface CheckoutSessionResponse {
  checkout_url: string
  session_id: string
}

export interface ApiError {
  detail: string
}
