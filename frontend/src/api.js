import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 300000,
})

export function getApiErrorMessage(error, fallback = '请求失败，请稍后重试。') {
  return error?.response?.data?.detail || error?.message || fallback
}

export async function getHealth() {
  const response = await apiClient.get('/health')
  return response.data
}

export async function uploadPdfs(files) {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))

  const response = await apiClient.post('/upload', formData)
  return response.data
}

export async function askQuestion({ question, modelProvider, topK }) {
  const response = await apiClient.post('/ask', {
    question,
    model_provider: modelProvider,
    top_k: topK,
  })
  return response.data
}

export async function generateStudyContent(taskType, modelProvider) {
  const routes = {
    summary: '/study/summary',
    knowledge_points: '/study/knowledge-points',
    quiz: '/study/quiz',
  }

  const route = routes[taskType]
  if (!route) {
    throw new Error('不支持的学习辅助类型。')
  }

  const response = await apiClient.post(route, {
    model_provider: modelProvider,
  })
  return response.data
}

export async function resetKnowledgeBase() {
  const response = await apiClient.post('/reset')
  return response.data
}
