import './Sidebar.css'

export default function Sidebar({ categories, active, onSelect, onChat }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span>📰</span>
        <div>
          <div className="logo-title">AI News</div>
          <div className="logo-sub">Personal Assistant</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section">Discover</div>
        {categories.map(c => (
          <button
            key={c.id}
            className={`nav-item ${active === c.id ? 'active' : ''}`}
            onClick={() => onSelect(c.id)}
          >
            <span className="nav-icon">{c.icon}</span>
            <span>{c.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="ai-btn" onClick={onChat}>
          <span>🤖</span> Ask AI Assistant
        </button>
      </div>
    </aside>
  )
}
