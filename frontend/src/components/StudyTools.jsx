import { useState } from 'react'
import { BookOpenCheck, ClipboardList, ListTree } from 'lucide-react'

import { generateStudyContent, getApiErrorMessage } from '../api'

const studyTasks = [
  {
    id: 'summary',
    label: '生成课程总结',
    description: '归纳课程主题、重点概念与学习建议。',
    icon: BookOpenCheck,
  },
  {
    id: 'knowledge_points',
    label: '提取核心知识点',
    description: '按课程模块整理知识点并给出解释。',
    icon: ListTree,
  },
  {
    id: 'quiz',
    label: '生成复习题',
    description: '生成选择、判断和简答题及参考答案。',
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
    <section className="panel study-panel" aria-labelledby="study-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">STUDY WORKBENCH</p>
          <h2 id="study-title">学习辅助</h2>
          <p>从知识库代表性片段中提炼课程资料，不脱离原始文档。</p>
        </div>
      </div>

      <div className="study-actions">
        {studyTasks.map((task) => {
          const Icon = task.icon
          const isLoading = activeTask === task.id
          return (
            <article className="study-action" key={task.id}>
              <Icon size={22} aria-hidden="true" />
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
