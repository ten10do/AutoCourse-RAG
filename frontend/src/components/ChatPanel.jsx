import { useState } from 'react'
import { MessageSquareText, Search, Send, Sparkles } from 'lucide-react'

import { askQuestion, getApiErrorMessage } from '../api'

export default function ChatPanel({ modelProvider, onResult }) {
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
      setResult({ ...payload, question: normalizedQuestion })
      onResult?.(payload)
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, '问答请求失败。'))
    } finally {
      setIsLoading(false)
    }
  }

  const sources = result?.sources || []

  return (
    <section className="chat-workspace" aria-labelledby="chat-title">
      <div className="workspace-hero">
        <div>
          <p className="eyebrow">AI STUDY WORKSPACE</p>
          <h1 id="chat-title">与知识库对话</h1>
          <p>
            基于已上传课程资料进行语义检索，回答会保留来源文件、页码和距离分数。
          </p>
        </div>
        <div className="hero-chip">
          <Sparkles size={17} />
          <span>{modelProvider}</span>
        </div>
      </div>

      <div className="chat-thread">
        {!result && !isLoading && (
          <div className="assistant-welcome">
            <div className="panel-icon" aria-hidden="true">
              <MessageSquareText size={21} />
            </div>
            <div>
              <h2>开始一次课程资料问答</h2>
              <p>
                例如：请总结自动控制系统中反馈控制的基本思想，并说明稳定性分析为什么重要。
              </p>
            </div>
          </div>
        )}

        {result?.question && (
          <div className="message-row user">
            <div className="message-bubble user-bubble">{result.question}</div>
          </div>
        )}

        {isLoading && (
          <div className="message-row assistant">
            <div className="message-bubble assistant-card loading-card">
              <span className="spinner dark" aria-hidden="true" />
              <span>正在检索知识库并生成回答...</span>
            </div>
          </div>
        )}

        {error && <div className="alert error" role="alert">{error}</div>}

        {result && (
          <div className="message-row assistant">
            <article className={`message-bubble assistant-card ${result.is_refused ? 'refused' : ''}`}>
              <div className="answer-label">
                <Search size={16} aria-hidden="true" />
                {result.is_refused ? '相关性不足' : `${modelProvider} 回答`}
              </div>
              <div className="rich-text">{result.answer}</div>
              {sources.length > 0 && (
                <div className="source-pills" aria-label="回答来源">
                  {sources.slice(0, 3).map((source, index) => (
                    <span key={`${source.source}-${source.page}-${index}`}>
                      {source.source} · 第 {source.page} 页
                    </span>
                  ))}
                  {sources.length > 3 && <span>+{sources.length - 3} 个来源</span>}
                </div>
              )}
            </article>
          </div>
        )}
      </div>

      <form className="chat-composer" onSubmit={handleSubmit}>
        <label className="field-label" htmlFor="question-input">
          课程问题
        </label>
        <textarea
          id="question-input"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="请输入你想向课程知识库提问的内容..."
          rows={3}
        />

        <div className="composer-footer">
          <label htmlFor="top-k">参考片段：{topK}</label>
          <input
            id="top-k"
            type="range"
            min="1"
            max="8"
            value={topK}
            onChange={(event) => setTopK(Number(event.target.value))}
          />
          <button className="send-button" type="submit" disabled={isLoading} aria-label="提交问题">
            {isLoading ? <span className="spinner" aria-hidden="true" /> : <Send size={19} />}
          </button>
        </div>
      </form>
    </section>
  )
}
