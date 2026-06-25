import { useState } from 'react'
import { BookOpenCheck, ClipboardList, ListTree } from 'lucide-react'

import { generateStudyContent, getApiErrorMessage } from '../api'

const studyTasks = [
  {
    id: 'summary',
    label: '生成课程总结',
    description: '归纳课程主要内容、核心主题、重点概念和学习建议。',
    icon: BookOpenCheck,
  },
  {
    id: 'knowledge_points',
    label: '提取核心知识点',
    description: '按模块整理自动化课程知识点，并给出简短解释。',
    icon: ListTree,
  },
  {
    id: 'quiz',
    label: '生成复习题',
    description: '生成选择题、判断题、简答题和参考答案。',
    icon: ClipboardList,
  },
]

export default function StudyTools({ modelProvider }) {
  const [activeTask, setActiveTask] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleGenerate = async (task) => {
    setActiveTask(task.id)
    setError('')
    try {
      const payload = await generateStudyContent(task.id, modelProvider)
      setResult({ title: task.label, content: payload.content })
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, '学习资料生成失败。'))
    } finally {
      setActiveTask('')
    }
  }

  return (
    <section className="study-panel" id="课程总结" aria-labelledby="study-title">
      <div className="study-panel-header">
        <div>
          <p className="eyebrow">STUDY TOOLS</p>
          <h2 id="study-title">学习辅助</h2>
          <p>从当前知识库中提炼课程总结、核心知识点和复习题。</p>
        </div>
      </div>

      <div className="study-actions">
        {studyTasks.map((task) => {
          const Icon = task.icon
          const isLoading = activeTask === task.id
          return (
            <article className="study-action" key={task.id}>
              <div className="study-icon">
                <Icon size={22} aria-hidden="true" />
              </div>
              <h3>{task.label}</h3>
              <p>{task.description}</p>
              <button
                className="button button-secondary"
                type="button"
                disabled={Boolean(activeTask)}
                onClick={() => handleGenerate(task)}
              >
                {isLoading && <span className="spinner dark" aria-hidden="true" />}
                {isLoading ? '生成中...' : task.label}
              </button>
            </article>
          )
        })}
      </div>

      {error && <div className="alert error" role="alert">{error}</div>}

      {result && (
        <div className="study-result">
          <div className="result-header">
            <span>生成结果</span>
            <strong>{result.title}</strong>
          </div>
          <div className="rich-text">{result.content}</div>
        </div>
      )}
    </section>
  )
}
