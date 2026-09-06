import { useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import NewsFeed from './components/NewsFeed.jsx'
import StockTicker from './components/StockTicker.jsx'
import ChatPanel from './components/ChatPanel.jsx'
import './App.css'

const CATEGORIES = [
  { id: 'general',       label: 'Top Stories',    icon: '🔥' },
  { id: 'technology',    label: 'Technology',      icon: '🤖' },
  { id: 'business',      label: 'Business',        icon: '📈' },
  { id: 'science',       label: 'Science',         icon: '🔬' },
  { id: 'health',        label: 'Health',          icon: '🏥' },
  { id: 'sports',        label: 'Sports',          icon: '⚽' },
  { id: 'entertainment', label: 'Entertainment',   icon: '🎬' },
  { id: 'world',         label: 'World',           icon: '🌍' },
]

export default function App() {
  const [activeCategory, setActiveCategory] = useState('general')
  const [chatOpen, setChatOpen] = useState(false)

  return (
    <div className="layout">
      <Sidebar
        categories={CATEGORIES}
        active={activeCategory}
        onSelect={setActiveCategory}
        onChat={() => setChatOpen(true)}
      />
      <div className="main-col">
        <StockTicker />
        <NewsFeed category={activeCategory} />
      </div>
      {chatOpen && <ChatPanel onClose={() => setChatOpen(false)} />}
      {!chatOpen && (
        <button className="chat-fab" onClick={() => setChatOpen(true)} title="Ask AI">
          💬
        </button>
      )}
    </div>
  )
}
