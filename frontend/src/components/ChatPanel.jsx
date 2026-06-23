import { useState } from 'react'
import { MessageSquareText, Search, Send } from 'lucide-react'

import { askQuestion, getApiErrorMessage } from '../api'
import SourceCard from './SourceCard'

export default function ChatPanel({ modelProvider }) {
  const [question, setQuestion] = useState('')
  const [topK, setTopK] = useState(4)
  const [result, setResult] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    const normalizedQuestion = question.trim()
    if (!normalizedQuestion) {
      setError('请输入与课程资料相关的问题。')
      return
    }

    setError('')
    setIsLoading(true)
    try {
      const payload = await askQuestion({
        question: normalizedQuestion,
        modelProvider,
        topK,
      })
      setResult(payload)
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, '问答请求失败。'))
    } finally {
      setIsLoading(false)
    }
  }

  const sources = result?.sources || []

  return (
    <>
      <section className="panel" aria-labelledby="chat-title">
        <div className="panel-heading">
          <div className="panel-icon" aria-hidden="true">
            <MessageSquareText size={21} />
          </div>
          <div>
            <p className="eyebrow">RAG QUERY</p>
            <h2 id="chat-title">智能问答</h2>
            <p>检索课程知识库，并基于可信片段生成可追溯回答。</p>
          </div>
        </div>

        <form className="chat-form" onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="question-input">
            课程问题
          </label>
          <textarea
            id="question-input"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="例如：PLC 的扫描周期是什么？"
            rows={4}
          />

          <div className="chat-controls">
            <label htmlFor="top-k">参考片段：{topK}</label>
            <input
              id="top-k"
              type="range"
              min="1"
              max="8"
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
            />
            <button className="button button-primary" type="submit" disabled={isLoading}>
              {isLoading ? <span className="spinner" aria-hidden="true" /> : <Send size={17} />}
              {isLoading ? '正在生成...' : '提交问题'}
            </button>
          </div>
        </form>

        {error && <div className="alert error" role="alert">{error}</div>}

        {result && (
          <div className={`answer-surface ${result.is_refused ? 'refused' : ''}`}>
            <div className="answer-label">
              <Search size={16} aria-hidden="true" />
              {result.is_refused ? '相关性不足' : `${modelProvider} 回答`}
            </div>
            <div className="rich-text">{result.answer}</div>
          </div>
        )}
      </section>

      <section className="panel sources-panel" aria-labelledby="sources-title">
        <div className="panel-heading compact">
          <div>
            <p className="eyebrow">TRACEABILITY</p>
            <h2 id="sources-title">参考来源</h2>
          </div>
          <span className="count-badge">{sources.length} 条</span>
        </div>

        {sources.length > 0 ? (
          <div className="source-list">
            {sources.map((source, index) => (
              <SourceCard
                key={`${source.source}-${source.page}-${index}`}
                source={source}
                index={index}
              />
            ))}
          </div>
        ) : (
          <div className="empty-state">提交问题后，检索来源将在此处展示。</div>
        )}
      </section>
    </>
  )
}
