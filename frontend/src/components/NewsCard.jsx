import './NewsCard.css'

const CAT_COLORS = {
  technology: '#4f6ef7', business: '#22c55e', science: '#a855f7',
  health: '#f59e0b', sports: '#ef4444', entertainment: '#ec4899',
  world: '#06b6d4', general: '#6366f1',
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function NewsCard({ article, featured }) {
  const color = CAT_COLORS[article.category] || '#6366f1'

  return (
    <a
      href={article.url !== '#' ? article.url : undefined}
      target="_blank"
      rel="noopener noreferrer"
      className={`news-card ${featured ? 'featured' : ''}`}
      style={{ '--accent': color }}
    >
      {article.image && (
        <div className="card-img-wrap">
          <img
            src={article.image}
            alt={article.title}
            className="card-img"
            onError={e => { e.target.parentElement.style.display = 'none' }}
          />
        </div>
      )}
      <div className="card-body">
        <div className="card-meta">
          <span className="card-badge" style={{ background: color + '22', color }}>
            {article.category}
          </span>
          <span className="card-source">{article.source}</span>
          <span className="card-time">{timeAgo(article.published_at)}</span>
        </div>
        <h2 className="card-title">{article.title}</h2>
        <p className="card-desc">{article.description}</p>
        {article.url && article.url !== '#' && (
          <span className="card-link">Read more →</span>
        )}
      </div>
    </a>
  )
}
