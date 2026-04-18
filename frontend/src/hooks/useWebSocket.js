// hooks/useWebSocket.js
import { useEffect, useRef, useState } from 'react'

export function useWebSocket(url) {
  const ws = useRef(null)
  const [messages, setMessages] = useState([])

  useEffect(() => {
    ws.current = new WebSocket(url)
    ws.current.onmessage = (e) => setMessages((prev) => [...prev, JSON.parse(e.data)])
    return () => ws.current?.close()
  }, [url])

  return messages
}
