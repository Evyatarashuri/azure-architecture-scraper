import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}` : '/api'
const timeout = Number(import.meta.env.VITE_API_TIMEOUT_MS ?? '60000')

export const api = axios.create({
  baseURL,
  timeout,
})
