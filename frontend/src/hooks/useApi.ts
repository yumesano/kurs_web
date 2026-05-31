import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../lib/apiClient'
import { CheckoutSessionResponse, Invoice, Payment, Plan, Subscription, User } from '../types'
import { AxiosError } from 'axios'

// ── Plans ─────────────────────────────────────────────────────────────────
export function usePlans() {
  return useQuery<Plan[]>({
    queryKey: ['plans'],
    queryFn: async () => {
      const { data } = await apiClient.get('/plans/')
      return data
    },
  })
}

export function usePlan(id: number) {
  return useQuery<Plan>({
    queryKey: ['plans', id],
    queryFn: async () => {
      const { data } = await apiClient.get(`/plans/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useCreatePlan() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (planData: Partial<Plan>) => {
      const { data } = await apiClient.post('/plans/', planData)
      return data as Plan
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['plans'] }),
  })
}

export function useUpdatePlan() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...planData }: Partial<Plan> & { id: number }) => {
      const { data } = await apiClient.patch(`/plans/${id}`, planData)
      return data as Plan
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['plans'] }),
  })
}

// ── Subscriptions ─────────────────────────────────────────────────────────
export function useMySubscriptions() {
  return useQuery<Subscription[]>({
    queryKey: ['subscriptions', 'me'],
    queryFn: async () => {
      const { data } = await apiClient.get('/subscriptions/')
      return data
    },
  })
}

export function useAllSubscriptions() {
  return useQuery<Subscription[]>({
    queryKey: ['subscriptions', 'all'],
    queryFn: async () => {
      const { data } = await apiClient.get('/subscriptions/admin/all')
      return data
    },
  })
}

export function useCreateCheckout() {
  return useMutation({
    mutationFn: async (planId: number) => {
      const { data } = await apiClient.post('/subscriptions/checkout', {
        plan_id: planId,
      })
      return data as CheckoutSessionResponse
    },
  })
}

export function useCancelSubscription() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (subscriptionId: number) => {
      const { data } = await apiClient.post(
        `/subscriptions/${subscriptionId}/cancel`,
      )
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['subscriptions'] }),
  })
}

// ── Invoices ──────────────────────────────────────────────────────────────
export function useMyInvoices() {
  return useQuery<Invoice[]>({
    queryKey: ['invoices', 'me'],
    queryFn: async () => {
      const { data } = await apiClient.get('/billing/invoices')
      return data
    },
  })
}

export function useAllInvoices() {
  return useQuery<Invoice[]>({
    queryKey: ['invoices', 'all'],
    queryFn: async () => {
      const { data } = await apiClient.get('/billing/admin/invoices')
      return data
    },
  })
}

// ── Payments ──────────────────────────────────────────────────────────────
export function useMyPayments() {
  return useQuery<Payment[]>({
    queryKey: ['payments', 'me'],
    queryFn: async () => {
      const { data } = await apiClient.get('/billing/payments')
      return data
    },
  })
}

export function useAllPayments() {
  return useQuery<Payment[]>({
    queryKey: ['payments', 'all'],
    queryFn: async () => {
      const { data } = await apiClient.get('/billing/admin/payments')
      return data
    },
  })
}

// ── Users (admin) ─────────────────────────────────────────────────────────
export function useAllUsers() {
  return useQuery<User[]>({
    queryKey: ['users', 'all'],
    queryFn: async () => {
      const { data } = await apiClient.get('/users/')
      return data
    },
  })
}

export function useUpdateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...userData }: { id: number; [key: string]: unknown }) => {
      const { data } = await apiClient.patch(`/users/${id}`, userData)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })
}

// ── Helpers ───────────────────────────────────────────────────────────────
export function getApiErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    return error.response?.data?.detail || 'Произошла ошибка'
  }
  return 'Неизвестная ошибка'
}
