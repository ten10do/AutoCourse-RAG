import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import { askQuestion, resetKnowledgeBase } from './api'

vi.mock('./api', () => ({
  getHealth: vi.fn().mockResolvedValue({
    status: 'ok',
    knowledge_base_ready: true,
    pdf_count: 2,
  }),
  uploadPdfs: vi.fn(),
  askQuestion: vi.fn(),
  generateStudyContent: vi.fn(),
  resetKnowledgeBase: vi.fn(),
}))

describe('AutoCourse-RAG React application', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  it('renders the required frontend modules and backend status', async () => {
    render(<App />)

    expect(
      screen.getByText('AutoCourse-RAG｜自动化课程智能问答与学习辅助系统'),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('模型选择')).toBeInTheDocument()
    expect(screen.getByText('多 PDF 上传')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '智能问答' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '参考来源' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '学习辅助' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '生成课程总结' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '提取核心知识点' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '生成复习题' })).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('知识库已就绪')).toBeInTheDocument()
    })
  })

  it('clears stale answers after the knowledge base is reset', async () => {
    askQuestion.mockResolvedValueOnce({
      answer: '当前知识库回答',
      sources: [],
      is_refused: false,
    })
    resetKnowledgeBase.mockResolvedValueOnce({ message: '知识库已清空。' })
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<App />)

    fireEvent.change(screen.getByLabelText('课程问题'), {
      target: { value: '什么是 PLC 扫描周期？' },
    })
    fireEvent.click(screen.getByRole('button', { name: '提交问题' }))

    expect(await screen.findByText('当前知识库回答')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '清空知识库' }))

    await waitFor(() => {
      expect(screen.queryByText('当前知识库回答')).not.toBeInTheDocument()
    })
  })
})
