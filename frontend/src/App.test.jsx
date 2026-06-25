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
  getApiErrorMessage: vi.fn((error, fallback) => error?.message || fallback),
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

    expect(screen.getByText('AutoCourse RAG')).toBeInTheDocument()
    expect(screen.getByText('自动化课程智能学习平台')).toBeInTheDocument()
    expect(screen.getAllByLabelText('模型选择')[0]).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '上传 PDF' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '与知识库对话' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '来源追溯' })).toBeInTheDocument()
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
    fireEvent.click(screen.getByLabelText('提交问题'))

    expect(await screen.findByText('当前知识库回答')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '清空知识库' }))

    await waitFor(() => {
      expect(screen.queryByText('当前知识库回答')).not.toBeInTheDocument()
    })
  })
})
