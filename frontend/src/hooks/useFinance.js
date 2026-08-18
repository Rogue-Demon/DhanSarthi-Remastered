import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, ENDPOINTS } from '@/services/api'

// --- Profile / Persona Queries & Mutations ---

export const useProfileQuery = () => {
  return useQuery({
    queryKey: ['profile'],
    queryFn: () => apiClient.get(ENDPOINTS.profile.get),
  })
}

export const useUpdateProfile = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => apiClient.patch(ENDPOINTS.profile.update, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
    },
  })
}

// --- Dashboard & Summary Queries ---

export const useDashboardData = (filters = {}) => {
  return useQuery({
    queryKey: ['dashboard', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.date_from) params.append('date_from', filters.date_from)
      if (filters.date_to) params.append('date_to', filters.date_to)

      const queryString = params.toString()
      const url = ENDPOINTS.dashboard.get + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

export const useFinancialSummary = (filters = {}) => {
  return useQuery({
    queryKey: ['financial-summary', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.date_from) params.append('date_from', filters.date_from)
      if (filters.date_to) params.append('date_to', filters.date_to)

      const queryString = params.toString()
      const url = ENDPOINTS.financial.summary + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

export const useCashFlow = (filters = {}) => {
  return useQuery({
    queryKey: ['cash-flow', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.date_from) params.append('date_from', filters.date_from)
      if (filters.date_to) params.append('date_to', filters.date_to)

      const queryString = params.toString()
      const url = ENDPOINTS.financial.cashFlow + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

// --- Income Hooks ---

export const useIncome = (filters = {}) => {
  return useQuery({
    queryKey: ['income', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.page) params.append('page', filters.page)
      if (filters.page_size) params.append('page_size', filters.page_size)
      if (filters.date_from) params.append('date_from', filters.date_from)
      if (filters.date_to) params.append('date_to', filters.date_to)
      if (filters.category) params.append('category', filters.category)
      if (filters.frequency) params.append('frequency', filters.frequency)

      const queryString = params.toString()
      const url = ENDPOINTS.income.list + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

export const useCreateIncome = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => apiClient.post(ENDPOINTS.income.create, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['income'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['cash-flow'] })
    },
  })
}

export const useUpdateIncome = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => apiClient.patch(ENDPOINTS.income.update(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['income'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['cash-flow'] })
    },
  })
}

export const useDeleteIncome = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => apiClient.delete(ENDPOINTS.income.delete(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['income'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['cash-flow'] })
    },
  })
}

// --- Expenses Hooks ---

export const useExpenses = (filters = {}) => {
  return useQuery({
    queryKey: ['expenses', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.page) params.append('page', filters.page)
      if (filters.page_size) params.append('page_size', filters.page_size)
      if (filters.date_from) params.append('date_from', filters.date_from)
      if (filters.date_to) params.append('date_to', filters.date_to)
      if (filters.category) params.append('category', filters.category)
      if (filters.frequency) params.append('frequency', filters.frequency)

      const queryString = params.toString()
      const url = ENDPOINTS.expenses.list + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

export const useCreateExpense = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => apiClient.post(ENDPOINTS.expenses.create, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['cash-flow'] })
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useUpdateExpense = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => apiClient.patch(ENDPOINTS.expenses.update(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['cash-flow'] })
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useDeleteExpense = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => apiClient.delete(ENDPOINTS.expenses.delete(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['cash-flow'] })
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

// --- Transactions Hooks ---

export const useTransactions = (filters = {}) => {
  return useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.page) params.append('page', filters.page)
      if (filters.page_size) params.append('page_size', filters.page_size)
      if (filters.date_from) params.append('date_from', filters.date_from)
      if (filters.date_to) params.append('date_to', filters.date_to)
      if (filters.category) params.append('category', filters.category)
      if (filters.transaction_type) params.append('transaction_type', filters.transaction_type)

      const queryString = params.toString()
      const url = ENDPOINTS.transactions.list + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

export const useCreateTransaction = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => apiClient.post(ENDPOINTS.transactions.create, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['income'] })
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['cash-flow'] })
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useUpdateTransaction = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => apiClient.patch(ENDPOINTS.transactions.update(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['income'] })
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['cash-flow'] })
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useDeleteTransaction = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => apiClient.delete(ENDPOINTS.transactions.delete(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['income'] })
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['cash-flow'] })
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

// --- Assets Hooks ---

export const useAssets = (filters = {}) => {
  return useQuery({
    queryKey: ['assets', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.page) params.append('page', filters.page)
      if (filters.page_size) params.append('page_size', filters.page_size)
      if (filters.asset_type) params.append('asset_type', filters.asset_type)

      const queryString = params.toString()
      const url = ENDPOINTS.assets.list + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

export const useCreateAsset = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => apiClient.post(ENDPOINTS.assets.create, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useUpdateAsset = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => apiClient.patch(ENDPOINTS.assets.update(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useDeleteAsset = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => apiClient.delete(ENDPOINTS.assets.delete(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

// --- Liabilities Hooks ---

export const useLiabilities = (filters = {}) => {
  return useQuery({
    queryKey: ['liabilities', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.page) params.append('page', filters.page)
      if (filters.page_size) params.append('page_size', filters.page_size)
      if (filters.liability_type) params.append('liability_type', filters.liability_type)

      const queryString = params.toString()
      const url = ENDPOINTS.liabilities.list + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

export const useCreateLiability = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => apiClient.post(ENDPOINTS.liabilities.create, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['liabilities'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useUpdateLiability = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => apiClient.patch(ENDPOINTS.liabilities.update(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['liabilities'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useDeleteLiability = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => apiClient.delete(ENDPOINTS.liabilities.delete(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['liabilities'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

// --- Budgets Hooks ---

export const useBudgets = (filters = {}) => {
  return useQuery({
    queryKey: ['budgets', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.page) params.append('page', filters.page)
      if (filters.page_size) params.append('page_size', filters.page_size)
      if (filters.category) params.append('category', filters.category)
      if (filters.period) params.append('period', filters.period)

      const queryString = params.toString()
      const url = ENDPOINTS.budgets.list + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

export const useCreateBudget = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => apiClient.post(ENDPOINTS.budgets.create, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useUpdateBudget = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => apiClient.patch(ENDPOINTS.budgets.update(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useDeleteBudget = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => apiClient.delete(ENDPOINTS.budgets.delete(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

// --- Goals Hooks ---

export const useGoals = (filters = {}) => {
  return useQuery({
    queryKey: ['goals', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.page) params.append('page', filters.page)
      if (filters.page_size) params.append('page_size', filters.page_size)
      if (filters.status) params.append('status', filters.status)
      if (filters.priority) params.append('priority', filters.priority)

      const queryString = params.toString()
      const url = ENDPOINTS.goals.list + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

export const useCreateGoal = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => apiClient.post(ENDPOINTS.goals.create, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useUpdateGoal = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => apiClient.patch(ENDPOINTS.goals.update(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useDeleteGoal = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => apiClient.delete(ENDPOINTS.goals.delete(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

// --- Loans Hooks ---

export const useLoans = (filters = {}) => {
  return useQuery({
    queryKey: ['loans', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.page) params.append('page', filters.page)
      if (filters.page_size) params.append('page_size', filters.page_size)
      if (filters.loan_type) params.append('loan_type', filters.loan_type)
      if (filters.status) params.append('status', filters.status)

      const queryString = params.toString()
      const url = ENDPOINTS.loans.list + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

export const useCreateLoan = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => apiClient.post(ENDPOINTS.loans.create, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loans'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useUpdateLoan = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => apiClient.patch(ENDPOINTS.loans.update(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loans'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useDeleteLoan = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => apiClient.delete(ENDPOINTS.loans.delete(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loans'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

// --- Financial Intelligence Hooks ---

export const useFinancialIntelligence = (insightType, filters = {}) => {
  return useQuery({
    queryKey: ['financial-intelligence', insightType, filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.date_from) params.append('date_from', filters.date_from)
      if (filters.date_to) params.append('date_to', filters.date_to)

      const queryString = params.toString()
      const endpoint = ENDPOINTS.financialIntelligence[insightType]
      if (!endpoint) throw new Error(`Invalid insight type: ${insightType}`)

      const url = endpoint + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

// --- Investments Hooks ---

export const useInvestments = (filters = {}) => {
  return useQuery({
    queryKey: ['investments', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.page) params.append('page', filters.page)
      if (filters.page_size) params.append('page_size', filters.page_size)
      if (filters.investment_type) params.append('investment_type', filters.investment_type)

      const queryString = params.toString()
      const url = ENDPOINTS.investments.list + (queryString ? `?${queryString}` : '')
      return apiClient.get(url)
    },
  })
}

export const useCreateInvestment = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => apiClient.post(ENDPOINTS.investments.create, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio-estimated'] })
      queryClient.invalidateQueries({ queryKey: ['investment-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useUpdateInvestment = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => apiClient.patch(ENDPOINTS.investments.update(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio-estimated'] })
      queryClient.invalidateQueries({ queryKey: ['investment-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useDeleteInvestment = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => apiClient.delete(ENDPOINTS.investments.delete(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio-estimated'] })
      queryClient.invalidateQueries({ queryKey: ['investment-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

export const useInvestmentSummary = () => {
  return useQuery({
    queryKey: ['investment-summary'],
    queryFn: () => apiClient.get(ENDPOINTS.financial.investmentsSummary),
  })
}

export const useEstimatedPortfolio = () => {
  return useQuery({
    queryKey: ['portfolio-estimated'],
    queryFn: () => apiClient.get(ENDPOINTS.market.portfolioEstimated),
  })
}

// --- Market Data Hooks ---

export const useStocksSearch = (query) => {
  return useQuery({
    queryKey: ['market-stocks-search', query],
    queryFn: () => apiClient.get(`${ENDPOINTS.market.stocksSearch}?q=${encodeURIComponent(query)}`),
    enabled: !!query,
  })
}

export const useStockQuote = (symbol) => {
  return useQuery({
    queryKey: ['market-stock-quote', symbol],
    queryFn: () => apiClient.get(ENDPOINTS.market.stocksQuote(symbol)),
    enabled: !!symbol,
  })
}

export const useMutualFundsSearch = (query) => {
  return useQuery({
    queryKey: ['market-mutual-funds-search', query],
    queryFn: () =>
      apiClient.get(`${ENDPOINTS.market.mutualFundsSearch}?q=${encodeURIComponent(query)}`),
    enabled: !!query,
  })
}

export const useMutualFundNav = (schemeId) => {
  return useQuery({
    queryKey: ['market-mutual-fund-nav', schemeId],
    queryFn: () => apiClient.get(ENDPOINTS.market.mutualFundsNav(schemeId)),
    enabled: !!schemeId,
  })
}
