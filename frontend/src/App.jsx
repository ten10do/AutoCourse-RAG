import { useCallback, useEffect, useState } from 'react'

import {
  getApiErrorMessage,
  getHealth,
  resetKnowledgeBase,
  uploadPdfs,
} from './api'
import ChatPanel from './components/ChatPanel'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import SourcePanel from './components/SourcePanel'
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
  const [chatResult, setChatResult] = useState(null)

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
        message: `知识库构建完成：${payload.page_count} 页，${payload.chunk_count} 个文本块。`,
      })
      setFiles([])
      setChatResult(null)
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
    if (!window.confirm('确定清空当前课程资料和知识库吗？')) return

    setIsResetting(true)
    try {
      await resetKnowledgeBase()
      setFiles([])
      setChatResult(null)
      setUploadFeedback({ type: 'success', message: '知识库已清空，请重新上传课程资料。' })
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
      <Header
        modelProvider={modelProvider}
        onModelProviderChange={setModelProvider}
        health={health}
        connectionError={connectionError}
      />

      <div className="workspace-grid">
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

        <main className="main-content" aria-label="AI 学习工作台">
          {connectionError && (
            <div className="alert error connection-alert" role="alert">
              {connectionError} 请先确认后端服务已启动或线上接口可访问。
            </div>
          )}

          <ChatPanel
            key={`chat-${knowledgeBaseRevision}`}
            modelProvider={modelProvider}
            onResult={setChatResult}
            knowledgeBaseRevision={knowledgeBaseRevision}
          />

          <StudyTools key={`study-${knowledgeBaseRevision}`} modelProvider={modelProvider} />
        </main>

        <SourcePanel sources={chatResult?.sources || []} />
      </div>
    </div>
  )
}
