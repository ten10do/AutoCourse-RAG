import { describe, expect, it, vi } from 'vitest'

const { clientMock, createMock } = vi.hoisted(() => {
  const clientMock = {
    get: vi.fn(),
    post: vi.fn(),
  }
  return {
    clientMock,
    createMock: vi.fn(() => clientMock),
  }
})

vi.mock('axios', () => ({
  default: {
    create: createMock,
  },
}))

const { askQuestion, getApiErrorMessage } = await import('./api')

describe('API client configuration', () => {
  it('uses the local FastAPI server when no development URL is configured', () => {
    expect(createMock).toHaveBeenCalledWith(
      expect.objectContaining({ baseURL: 'http://localhost:8000' }),
    )
  })

  it('maps optional conversation fields onto the compatible ask payload', async () => {
    clientMock.post.mockResolvedValueOnce({ data: { answer: '回答' } })

    await askQuestion({
      question: '其中积分项有什么作用？',
      modelProvider: 'Groq',
      topK: 4,
      conversationId: 'conversation-api',
      history: [{ role: 'user', content: '什么是 PID？' }],
      contextOptions: { max_recent_turns: 4 },
    })

    expect(clientMock.post).toHaveBeenCalledWith('/ask', {
      question: '其中积分项有什么作用？',
      model_provider: 'Groq',
      top_k: 4,
      conversation_id: 'conversation-api',
      history: [{ role: 'user', content: '什么是 PID？' }],
      context_options: { max_recent_turns: 4 },
    })
  })

  it('formats FastAPI validation detail arrays as a stable message', () => {
    const message = getApiErrorMessage(
      {
        response: {
          data: {
            detail: [
              {
                loc: ['body', 'history', 0, 'content'],
                msg: 'String should have at most 4000 characters',
              },
            ],
          },
        },
      },
      '请求失败',
    )

    expect(message).toBe(
      'history.0.content：String should have at most 4000 characters',
    )
  })
})
