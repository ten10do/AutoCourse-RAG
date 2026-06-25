import {
  BookOpenCheck,
  Brain,
  Cpu,
  Database,
  FileText,
  ListChecks,
  RotateCcw,
  Sparkles,
} from 'lucide-react'

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

  const navItems = [
    { label: '上传 PDF', icon: FileText, active: true },
    { label: '我的资料库', icon: Database },
    { label: '模型配置', icon: Cpu },
    { label: '课程总结', icon: BookOpenCheck },
    { label: '知识点提取', icon: Brain },
    { label: '复习题生成', icon: ListChecks },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-card nav-card">
        <div className="sidebar-title">
          <Sparkles size={18} aria-hidden="true" />
          <span>知识库导航</span>
        </div>

        <nav className="nav-list" aria-label="知识库导航">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <a className={item.active ? 'active' : ''} href={`#${item.label}`} key={item.label}>
                <Icon size={17} aria-hidden="true" />
                <span>{item.label}</span>
              </a>
            )
          })}
        </nav>
      </div>

      <section className="sidebar-card" id="模型配置" aria-labelledby="model-title">
        <div className="section-label-row">
          <Cpu size={18} aria-hidden="true" />
          <h2 id="model-title">模型配置</h2>
        </div>
        <label className="field-label" htmlFor="model-provider">
          当前大模型
        </label>
        <select
          id="model-provider"
          aria-label="模型选择"
          value={modelProvider}
          onChange={(event) => onModelProviderChange(event.target.value)}
        >
          <option value="DeepSeek">DeepSeek</option>
          <option value="Groq">Groq</option>
        </select>
      </section>

      <UploadPanel
        files={files}
        onFilesChange={onFilesChange}
        onBuild={onBuild}
        isUploading={isUploading}
        feedback={uploadFeedback}
      />

      <section className="sidebar-card" aria-labelledby="status-title">
        <div className="section-label-row">
          <Database size={18} aria-hidden="true" />
          <h2 id="status-title">知识库状态</h2>
        </div>
        <div className={`status-line ${connectionError ? 'offline' : 'online'}`}>
          <span className="status-dot" aria-hidden="true" />
          <span>{statusLabel}</span>
        </div>
        <p className="status-meta">已保存 PDF：{health.pdf_count ?? 0} 份</p>
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

      <section className="sidebar-card steps" aria-labelledby="steps-title">
        <h2 id="steps-title">使用步骤</h2>
        <ol>
          <li>选择 DeepSeek 或 Groq 模型。</li>
          <li>上传一份或多份课程 PDF。</li>
          <li>构建知识库后开始问答。</li>
          <li>查看来源追溯或生成学习资料。</li>
        </ol>
      </section>
    </aside>
  )
}
