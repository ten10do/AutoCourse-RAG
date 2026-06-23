import { Cpu, RotateCcw, Server, Workflow } from 'lucide-react'

import UploadPanel from './UploadPanel'

export default function Sidebar({
  modelProvider,
  onModelProviderChange,
  health,
  connectionError,
  files,
  onFilesChange,
  onBuild,
  isUploading,
  uploadFeedback,
  onReset,
  isResetting,
}) {
  const statusLabel = connectionError
    ? '后端未连接'
    : health.knowledge_base_ready
      ? '知识库已就绪'
      : '等待构建知识库'

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark" aria-hidden="true">
          <Workflow size={22} />
        </div>
        <div>
          <strong>AutoCourse</strong>
          <span>RAG Control Center</span>
        </div>
      </div>

      <section className="sidebar-section" aria-labelledby="model-title">
        <div className="section-label-row">
          <Cpu size={18} aria-hidden="true" />
          <h2 id="model-title">模型服务</h2>
        </div>
        <label className="field-label" htmlFor="model-provider">
          模型选择
        </label>
        <select
          id="model-provider"
          aria-label="模型选择"
          value={modelProvider}
          onChange={(event) => onModelProviderChange(event.target.value)}
        >
          <option value="Groq">Groq</option>
          <option value="DeepSeek">DeepSeek</option>
        </select>
      </section>

      <UploadPanel
        files={files}
        onFilesChange={onFilesChange}
        onBuild={onBuild}
        isUploading={isUploading}
        feedback={uploadFeedback}
      />

      <section className="sidebar-section" aria-labelledby="status-title">
        <div className="section-label-row">
          <Server size={18} aria-hidden="true" />
          <h2 id="status-title">后端状态</h2>
        </div>
        <div className={`status-line ${connectionError ? 'offline' : 'online'}`}>
          <span className="status-dot" aria-hidden="true" />
          <span>{statusLabel}</span>
        </div>
        <p className="status-meta">已保存 PDF：{health.pdf_count ?? 0} 个</p>
        <button
          className="button button-danger button-full"
          type="button"
          disabled={isResetting || Boolean(connectionError)}
          onClick={onReset}
        >
          {isResetting ? <span className="spinner" aria-hidden="true" /> : <RotateCcw size={17} />}
          {isResetting ? '正在清空...' : '清空知识库'}
        </button>
      </section>

      <section className="sidebar-section steps" aria-labelledby="steps-title">
        <h2 id="steps-title">使用步骤</h2>
        <ol>
          <li>选择模型服务</li>
          <li>上传课程 PDF</li>
          <li>构建课程知识库</li>
          <li>提问或生成学习资料</li>
        </ol>
      </section>
    </aside>
  )
}
