import { describe, expect, it, vi } from 'vitest'

const { createMock } = vi.hoisted(() => ({
  createMock: vi.fn(() => ({
    get: vi.fn(),
    post: vi.fn(),
  })),
}))

vi.mock('axios', () => ({
  default: {
    create: createMock,
  },
}))

await import('./api')

describe('API client configuration', () => {
  it('uses the local FastAPI server when no development URL is configured', () => {
    expect(createMock).toHaveBeenCalledWith(
      expect.objectContaining({ baseURL: 'http://localhost:8000' }),
    )
  })
})
