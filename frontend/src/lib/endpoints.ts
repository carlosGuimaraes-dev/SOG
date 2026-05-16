export const ENDPOINTS = {
  LOGIN: '/auth/login',
  ME: '/auth/me',
  LOGOUT: '/auth/logout',
  REFRESH: '/auth/refresh',
  PROCESSOS: '/processos',
  HISTORICO: '/historico',
  APROVAR: (id: number | string) => `/aprovar/${id}`,
  REJEITAR: (id: number | string) => `/rejeitar/${id}`,
  SCREENSHOT: (id: number | string) => `/processos/${id}/screenshot`,
} as const
