import { useCallback, useEffect, useState } from 'react'
import { Activity, Braces, DatabaseZap } from 'lucide-react'

import {
  getApiErrorMessage,
  getHealth,
  resetKnowledgeBase,
  uploadPdfs,
} from './api'
import ChatPanel from './components/ChatPanel'
import Sidebar from './components/Sidebar'
import StudyTools from './components/StudyTools'

const initialHealth = {
  status: 'loading',
  knowledge_base_ready: false,
  pdf_count: 0,
}

export default function App() {
  const [modelProvider, setModelProvider] = useState('Groq')
  const [health, setHealth] = useState(initialHealth)
  const [connectionError, setConnectionError] = useState('')
  const [files, setFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [isResetting, setIsResetting] = useState(false)
  const [uploadFeedback, setUploadFeedback] = useState(null)
  const [knowledgeBaseRevision, setKnowledgeBaseRevision] = useState(0)

  const refreshHealth = useCallback(async () => {
    try {
      const payload = await getHealth()
      setHealth(payload)
      setConnectionError('')
    } catch (error) {
      setConnectionError(getApiErrorMessage(error, '无法连接 FastAPI 后端。'))
    }
  }, [])

  useEffect(() => {
    refreshHealth()
  }, [refreshHealth])

  const handleBuild = async () => {
    if (files.length === 0) return

    setIsUploading(true)
    setUploadFeedback(null)
    try {
      const payload = await uploadPdfs(files)
      setUploadFeedback({
        type: 'success',
        message: `构建完成：${payload.page_count} 页，${payload.chunk_count} 个文本块。`,
      })
      setFiles([])
      setKnowledgeBaseRevision((revision) => revision + 1)
      await refreshHealth()
    } catch (error) {
      setUploadFeedback({
        type: 'error',
        message: getApiErrorMessage(error, '知识库构建失败。'),
      })
    } finally {
      setIsUploading(false)
    }
  }

  const handleReset = async () => {
    if (!window.confirm('确定清空当前课程资料和向量知识库吗？')) return

    setIsResetting(true)
    try {
      await resetKnowledgeBase()
      setFiles([])
      setUploadFeedback({ type: 'success', message: '知识库已清空。' })
      setKnowledgeBaseRevision((revision) => revision + 1)
      await refreshHealth()
    } catch (error) {
      setUploadFeedback({
        type: 'error',
        message: getApiErrorMessage(error, '知识库清空失败。'),
      })
    } finally {
      setIsResetting(false)
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        modelProvider={modelProvider}
        onModelProviderChange={setModelProvider}
        health={health}
        connectionError={connectionError}
        files={files}
        onFilesChange={setFiles}
        onBuild={handleBuild}
        isUploading={isUploading}
        uploadFeedback={uploadFeedback}
        onReset={handleReset}
        isResetting={isResetting}
      />

      <main className="main-content">
        <header className="product-header">
          <div>
            <div className="product-kicker">
              <Activity size={16} aria-hidden="true" />
              INDUSTRIAL KNOWLEDGE SYSTEM
            </div>
            <h1>AutoCourse-RAG｜自动化课程智能问答与学习辅助系统</h1>
            <p>React 操作台连接 FastAPI 与本地 RAG 知识库，提供问答、来源追溯和学习资料生成。</p>
          </div>
          <div className="technology-badges" aria-label="技术架构">
            <span><Braces size={15} /> React</span>
            <span><DatabaseZap size={15} /> FastAPI + RAG</span>
          </div>
        </header>

        {connectionError && (
          <div className="alert error connection-alert" role="alert">
            {connectionError} 请先启动后端服务。
          </div>
        )}

        <div className="content-grid">
          <div className="primary-column">
            <ChatPanel key={`chat-${knowledgeBaseRevision}`} modelProvider={modelProvider} />
          </div>
          <div className="secondary-column">
            <StudyTools key={`study-${knowledgeBaseRevision}`} modelProvider={modelProvider} />
          </div>
        </div>
      </main>
    </div>
  )
}
