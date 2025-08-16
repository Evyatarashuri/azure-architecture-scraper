import { api } from './client'

export type AskRequest = { question: string }
export type AskResponse = {
  answer?: string
  sources?: Array<{ title?: string; url?: string }>
  [k: string]: unknown
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const res = await api.post<AskResponse>(
    '/query',
    { question } as AskRequest,
    { baseURL: '', timeout: 120000 }
  )
  return res.data
}
