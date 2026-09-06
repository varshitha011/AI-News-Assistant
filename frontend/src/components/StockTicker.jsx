import { useEffect, useState } from 'react'
import { getStocks } from '../api.js'
import './StockTicker.css'

export default function StockTicker() {
  const [quotes, setQuotes] = useState([])

  useEffect(() => {
    getStocks().then(d => setQuotes(d.quotes || [])).catch(() => {})
  }, [])

  if (!quotes.length) return null

  const validQuotes = quotes.filter(q => q.price !== null && !q.error)
  if (!validQuotes.length) return null

  return (
    <div className="ticker-wrap">
      <div className="ticker-label">📈 Markets</div>
      <div className="ticker-track">
        {[...validQuotes, ...validQuotes].map((q, i) => (
          <span key={i} className={`ticker-item ${q.change >= 0 ? 'up' : 'down'}`}>
            <span className="t-symbol">{q.symbol.replace('.NS','').replace('^','')}</span>
            <span className="t-price">{q.price}</span>
            <span className="t-change">{q.change >= 0 ? '▲' : '▼'} {Math.abs(q.change_pct)}%</span>
          </span>
        ))}
      </div>
    </div>
  )
}
