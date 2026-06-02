# 基于 RAG 的自动化课程知识库问答系统

## 项目简介

本项目是一个面向自动化专业课程资料的 RAG 知识库问答系统。

用户可以上传自动控制原理、PLC、传感器、电机控制等课程 PDF，系统会自动完成 PDF 文本解析、文本切分、本地 Embedding 向量化、Chroma 向量数据库构建，并根据用户问题检索相关课程资料片段，再调用 Groq 大模型生成中文回答。

## 项目背景

普通大模型无法直接了解用户上传的私有课程资料，直接提问时容易出现知识不足或幻觉问题。

RAG，即 Retrieval-Augmented Generation，可以先从本地知识库中检索相关资料，再让大模型基于检索结果回答，从而提高回答的准确性和可追溯性。

本项目将 RAG 技术应用于自动化专业课程资料问答场景，适用于自动控制原理、PLC、传感器、电机控制等课程资料学习。

## 技术栈

- Python
- Streamlit
- LangChain
- Chroma
- HuggingFace Embeddings
- Groq API
- PyPDF
- python-dotenv

## 核心功能

- PDF 文件上传
- PDF 文本解析
- 文本分块处理
- 本地 Embedding 向量化
- Chroma 向量数据库存储
- 基于用户问题的语义检索
- Groq 大模型中文回答生成
- 参考片段和页码展示
- 本地知识库清空

## 项目流程

```text
上传课程 PDF
↓
PDF 文本解析
↓
文本切分
↓
本地 Embedding 向量化
↓
存入 Chroma 向量数据库
↓
用户输入问题
↓
语义检索相关文本块
↓
Groq 大模型生成回答
↓
展示回答和参考片段