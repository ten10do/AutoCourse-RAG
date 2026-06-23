# AutoCourse-RAG

面向自动化课程资料的智能问答与学习辅助系统

## 项目简介

AutoCourse-RAG 是一个采用 React + FastAPI 前后端分离架构的课程资料 RAG（Retrieval-Augmented Generation）应用。用户可以上传多份自动化课程 PDF，构建本地向量知识库，并通过 Groq 或 DeepSeek 模型完成课程问答、来源追溯、课程总结、知识点提取和复习题生成。

系统将大模型回答限制在课程资料检索结果内，并通过距离阈值拒绝相关性不足的问题，降低脱离资料生成内容的风险。项目同时保留原有 Streamlit 版本，便于对比单体应用与前后端分离架构的实现方式。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | HTML、CSS、JavaScript、React、Vite |
| 前端通信 | Axios、FormData、RESTful API |
| 后端 | Python、FastAPI、Uvicorn、Pydantic、CORS |
| RAG 框架 | LangChain、LangChain Community |
| 文档处理 | PyPDF、RecursiveCharacterTextSplitter |
| 向量化 | HuggingFace Embeddings、Sentence Transformers |
| 向量数据库 | Chroma |
| 大模型服务 | Groq API、DeepSeek API、OpenAI-compatible API |
| 测试 | unittest、FastAPI TestClient、Vitest、Testing Library |

## 系统架构

```mermaid
flowchart LR
    U[用户浏览器] --> F[React + Vite 前端]
    F -->|Axios / REST API| A[FastAPI 后端]
    A --> D[PDF 解析与文本切分]
    D --> E[HuggingFace Embeddings]
    E --> C[(Chroma 向量库)]
    A -->|语义检索| C
    C --> T{距离阈值判断}
    T -->|相关| L[Groq / DeepSeek]
    T -->|不相关| R[拒答]
    L --> F
    R --> F
```

RAG 处理链路：

```text
多 PDF 上传
  → PDF 文本解析
  → chunk 切分
  → HuggingFace Embedding
  → Chroma 持久化
  → similarity_search_with_score
  → 距离阈值判断
  → 大模型生成回答
  → 来源文件、页码、距离分数和参考片段展示
```

## 核心功能

- 支持一次上传多份 PDF，并统一构建课程知识库。
- 对每个文档执行文本解析、chunk 切分和本地 Embedding 向量化。
- 使用 Chroma 持久化存储向量，并通过 `similarity_search_with_score` 完成语义检索。
- 返回来源文件、页码、距离分数和参考片段，提供回答追溯能力。
- 根据 Chroma 距离值执行阈值判断，相关性不足时不调用大模型并直接拒答。
- 支持 Groq / DeepSeek 双模型切换，复用统一的大模型调用封装。
- 基于当前知识库生成课程总结、核心知识点和复习题。
- 支持清空 PDF 文件和向量库，并使用新资料重新构建知识库。

## 前端功能

前端使用 Vite + React + JavaScript 构建，采用原生 CSS 实现工业蓝灰风格和基础响应式布局。

- 使用 `Sidebar`、`UploadPanel`、`ChatPanel`、`SourceCard`、`StudyTools` 等组件拆分页面职责。
- 通过 Axios 统一封装健康检查、上传、问答、学习辅助和知识库重置请求。
- 支持拖拽或选择多份 PDF，并通过 `FormData` 上传至 FastAPI。
- 支持 Groq / DeepSeek 模型选择和检索片段数量调整。
- 展示请求 loading、接口错误、拒答、知识库状态和构建结果。
- 使用可折叠来源卡片收纳参考内容，避免长文本影响页面浏览。
- 在知识库清空或重建后同步刷新状态，并清除旧知识库对应的页面结果。
- 提供桌面双栏、平板和移动端单栏布局，无需引入复杂 UI 框架。

## 后端 API

FastAPI 提供以下接口，默认服务地址为 `http://localhost:8000`，交互式接口文档位于 `/docs`。

| 方法 | 路径 | 说明 | 主要请求数据 |
| --- | --- | --- | --- |
| `GET` | `/health` | 获取服务与知识库状态 | 无 |
| `POST` | `/upload` | 上传多份 PDF 并重建知识库 | `multipart/form-data`：`files` |
| `POST` | `/ask` | 执行检索、阈值判断和问答 | `question`、`model_provider`、`top_k` |
| `POST` | `/study/summary` | 生成课程总结 | `model_provider` |
| `POST` | `/study/knowledge-points` | 提取核心知识点 | `model_provider` |
| `POST` | `/study/quiz` | 生成复习题和参考答案 | `model_provider` |
| `POST` | `/reset` | 清空后端 PDF 与 Chroma 向量库 | 无 |

`POST /ask` 返回示例：

```json
{
  "answer": "基于课程资料生成的回答",
  "sources": [
    {
      "source": "course.pdf",
      "page": 3,
      "score": 9.25,
      "content": "用于生成回答的参考片段"
    }
  ],
  "is_refused": false
}
```

## 项目结构

```text
AutoCourse-RAG/
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用、请求模型和 REST API
│   ├── rag_core.py             # PDF 处理、向量库、检索与拒答逻辑
│   ├── llm_client.py           # Groq / DeepSeek 统一调用封装
│   ├── requirements.txt        # 后端依赖
│   └── test_main.py            # FastAPI 接口测试
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx
│   │   │   ├── UploadPanel.jsx
│   │   │   ├── ChatPanel.jsx
│   │   │   ├── SourceCard.jsx
│   │   │   └── StudyTools.jsx
│   │   ├── api.js              # Axios 接口封装
│   │   ├── App.jsx             # 前端状态管理与页面组合
│   │   ├── main.jsx            # React 入口
│   │   └── styles.css          # 原生 CSS 与响应式样式
│   ├── package.json
│   └── vite.config.js          # Vite 配置与开发代理
├── app.py                      # 保留的 Streamlit 版本
├── rag_core.py                 # Streamlit 版本 RAG 核心模块
├── llm_client.py               # Streamlit 版本模型调用模块
├── test_rag_core.py            # RAG 核心测试
├── requirements.txt            # Streamlit 版本依赖
├── screenshots/                # README 功能截图
├── .gitignore
└── README.md
```

运行时会生成以下目录，且不应提交到 Git：

```text
backend/data/        # FastAPI 后端保存的 PDF
backend/vector_db/   # FastAPI 后端 Chroma 数据
frontend/node_modules/
frontend/dist/
```

## 环境变量配置

在项目根目录创建 `.env` 文件：

```env
GROQ_API_KEY=你的Groq密钥
DEEPSEEK_API_KEY=你的DeepSeek密钥
```

不要在代码中写死密钥，也不要将 `.env` 提交到 GitHub。项目中的 `.gitignore` 已忽略 `.env`。

前端开发环境默认通过 Vite 的 `/api` 代理访问 `http://127.0.0.1:8000`。如需连接其他后端地址，可在前端环境中配置：

```env
VITE_API_BASE_URL=https://your-api.example.com
```

## 后端运行方式

建议使用 Python 虚拟环境：

```bash
python -m venv venv
```

安装 FastAPI 后端依赖：

```bash
pip install -r backend/requirements.txt
```

启动后端：

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

启动后可访问：

- 健康检查：`http://localhost:8000/health`
- Swagger API 文档：`http://localhost:8000/docs`

## 前端运行方式

安装 Node.js 依赖：

```bash
cd frontend
npm install
```

启动 React 开发服务器：

```bash
npm run dev
```

浏览器访问 `http://localhost:5173`。生产构建命令：

```bash
npm run build
```

## 功能截图

以下截图基于 React + FastAPI 版本和 3 份自动控制课程测试资料生成。

### React 前端首页

![React 前端首页](screenshots/01_react_home.png)

### 多 PDF 上传与知识库管理

![多 PDF 上传与知识库管理](screenshots/02_pdf_upload.png)

### RAG 智能问答

![RAG 智能问答](screenshots/03_rag_answer.png)

### 来源追溯与距离分数

![来源追溯与距离分数](screenshots/04_source_trace.png)

### 学习辅助

![学习辅助](screenshots/05_study_tools.png)

### 移动端响应式布局

![移动端响应式布局](screenshots/06_responsive_layout.png)

## 项目亮点

- **React 组件化开发**：按上传、问答、来源和学习辅助等职责拆分组件，通过 Props 与状态组合完整页面。
- **原生 Web 页面实现**：使用 HTML、CSS 和 JavaScript 完成正式、响应式的工业蓝灰界面，不依赖复杂 UI 框架。
- **前后端分离**：React 通过 Axios 调用 FastAPI RESTful API，接口职责和数据模型清晰。
- **完整 RAG 链路**：覆盖 PDF 解析、chunk 切分、Embedding、Chroma 持久化、语义检索、阈值判断和回答生成。
- **多文档知识库**：支持多份课程资料统一向量化，并保留每个 chunk 的来源文件和页码信息。
- **可解释与低幻觉设计**：展示检索距离和参考片段，相关性不足时跳过大模型调用并直接拒答。
- **双模型接入**：通过统一客户端封装 Groq 和 OpenAI-compatible DeepSeek API，前端可直接切换模型服务。
- **垂直场景落地**：围绕自动控制、PLC、传感器、电机控制等自动化课程资料提供问答和学习辅助能力。
- **新旧架构并存**：保留 Streamlit 实现，同时提供 React + FastAPI 版本，展示从快速原型到前后端分离应用的演进过程。

## 当前不足与后续优化

- 暂未集成 OCR，扫描版或无文本层 PDF 无法直接构建知识库。
- 当前采用基础向量相似度检索，后续可加入关键词混合检索和 Cross-Encoder 重排序。
- 距离阈值目前基于当前 Embedding 与课程资料设定，后续可通过检索评估数据进行校准。
- 学习辅助功能使用有限数量的代表性 chunk，后续可增加分层摘要和 Map-Reduce 总结。
- 暂未实现用户登录、知识库隔离和多知识库管理。
- 暂未支持多轮对话记忆，当前每次问答独立执行检索。
- 后续可增加检索指标评估、自动化端到端测试、容器化部署和持续集成。
