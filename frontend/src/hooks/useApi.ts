import { useEffect, useState } from 'react'
import { api } from '../api/client'

export function useApi<T = unknown>(path: string) {
    const [data, setData] = useState<T | null>(null)
    const [error, setError] = useState<string>('')
    const [loading, setLoading] = useState<boolean>(true)

    useEffect(() => {
        let mounted = true
        setLoading(true)
        api.get(path)
            .then((response) => {
                if (mounted) {
                    setData(response.data)
                    setError('')
                }
            })
            .catch((error) => {
                if (mounted) {
                    setData(null)
                    setError(error.message)
                }
            })
            .finally(() => {
                if (mounted) {
                    setLoading(false)
                }
            })

        return () => {
            mounted = false
        }
    }, [path])

    return { data, error, loading }
}