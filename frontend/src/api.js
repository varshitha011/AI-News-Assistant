const BASE = import.meta.env.VITE_API_URL || '/api'

export async function getNews(category = 'general', max = 10) {
  const r = await fetch(`${BASE}/news/${category}?max=${max}`)
  return r.json()
}

export async function searchNews(query) {
  const r = await fetch(`${BASE}/news/search/${encodeURIComponent(query)}`)
  return r.json()
}

export async function getStocks(symbols = '') {
  const r = await fetch(`${BASE}/stocks${symbols ? '?symbols=' + symbols : ''}`)
  return r.json()
}

export async function sendChat(messages, message) {
  const r = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, message }),
  })
  const data = await r.json()
  if (!r.ok) throw new Error(data.detail || 'Chat error')
  return data.reply
}
