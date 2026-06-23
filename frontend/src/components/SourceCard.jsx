import { ChevronDown, FileText } from 'lucide-react'

export default function SourceCard({ source, index }) {
  return (
    <details className="source-item">
      <summary>
        <span className="source-index">{String(index + 1).padStart(2, '0')}</span>
        <FileText size={17} aria-hidden="true" />
        <span className="source-title">{source.source}</span>
        <span className="source-meta">第 {source.page} 页</span>
        <span className="score-badge">距离 {source.score.toFixed(4)}</span>
        <ChevronDown className="source-chevron" size={17} aria-hidden="true" />
      </summary>
      <div className="source-content">{source.content}</div>
    </details>
  )
}
