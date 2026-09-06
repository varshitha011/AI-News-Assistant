import { useEffect, useState } from 'react'
import { getNews, searchNews } from '../api.js'
import NewsCard from './NewsCard.jsx'
import './NewsFeed.css'

export default function NewsFeed({ category }) {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [searching, setSearching] = useState(false)

  useEffect(() => {
    setLoading(true)
    setSearch('')
    getNews(category, 12)
      .then(d => setArticles(d.articles || []))
      .catch(() => setArticles([]))
      .finally(() => setLoading(false))
  }, [category])

  const handleSearch = async e => {
    e.preventDefault()
    if (!search.trim()) return
    setSearching(true)
    try {
      const d = await searchNews(search.trim())
      setArticles(d.articles || [])
    } finally { setSearching(false) }
  }

  const categoryLabels = {
    general: '🔥 Top Stories', technology: '🤖 Technology',
    business: '📈 Business', science: '🔬 Science',
    health: '🏥 Health', sports: '⚽ Sports',
    entertainment: '🎬 Entertainment', world: '🌍 World',
  }

  return (
    <div className="feed">
      <div className="feed-header">
        <h1 className="feed-title">{categoryLabels[category] || category}</h1>
        <form className="search-form" onSubmit={handleSearch}>
          <input
            className="search-input"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search news..."
          />
          <button className="search-btn" disabled={searching}>
            {searching ? '...' : '🔍'}
          </button>
        </form>
      </div>

      {loading ? (
        <div className="feed-loading">
          {[...Array(6)].map((_, i) => <div key={i} className="skeleton" />)}
        </div>
      ) : articles.length === 0 ? (
        <div className="feed-empty">No articles found.</div>
      ) : (
        <div className="feed-grid">
          {articles.map((a, i) => <NewsCard key={i} article={a} featured={i === 0} />)}
        </div>
      )}
    </div>
  )
}
