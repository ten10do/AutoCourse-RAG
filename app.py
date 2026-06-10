import os
import streamlit as st

from rag_core import (
    build_knowledge_base,
    retrieve_docs,
    has_relevant_docs,
    generate_answer,
    clear_knowledge_base,
    REFUSAL_MESSAGE
)


DATA_DIR = "data"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


st.set_page_config(
    page_title="自动化课程知识库问答系统",
    layout="wide"
)


st.title("基于 RAG 的自动化课程知识库问答系统")

st.markdown("""
本系统支持上传自动化专业课程 PDF，并基于 RAG 技术进行课程资料问答。

当前版本功能：

1. 上传 PDF 课程资料
2. 解析 PDF 文本
3. 使用本地 Embedding 模型生成向量
4. 使用 Chroma 保存向量数据库
5. 根据用户问题检索相关资料片段
6. 调用 Groq 大模型生成中文回答
7. 显示参考片段和页码来源
""")


with st.sidebar:
    st.header("1. 知识库管理")

    uploaded_files = st.file_uploader(
        "请上传自动化课程 PDF",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        file_paths = []

        for uploaded_file in uploaded_files:
            file_path = os.path.join(DATA_DIR, uploaded_file.name)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            file_paths.append(file_path)

        st.success(f"文件上传成功：共 {len(file_paths)} 个 PDF。")

        if st.button("建立/重新构建知识库"):
            try:
                with st.spinner("正在解析 PDF 并建立本地知识库，第一次运行可能较慢..."):
                    page_count, chunk_count = build_knowledge_base(file_paths)

                st.success(
                    f"知识库建立完成：共 {page_count} 页，生成 {chunk_count} 个文本块。"
                )

            except Exception as e:
                st.error("知识库建立失败。")
                st.write("错误原因：")
                st.code(str(e))
                st.warning(
                    "建议：请换一个文字版 PDF 测试。不要使用扫描版 PDF 或图片版教材。"
                )

    st.divider()

    if st.button("清空知识库"):
        clear_knowledge_base()
        st.success("知识库已清空，请重新上传课程资料。")


st.header("2. 课程知识问答")

st.markdown("""
你可以输入和 PDF 内容相关的问题，系统会先从知识库中检索相关资料片段，
再调用 Groq 大模型基于这些片段生成回答。

示例问题：

- 什么是闭环控制系统？
- PID 控制器有什么作用？
- PLC 的扫描周期是什么？
- 传感器的静态特性有哪些？
""")

question = st.text_input(
    "请输入你的问题",
    placeholder="例如：什么是闭环控制系统？"
)

top_k = st.slider(
    "返回参考片段数量",
    min_value=1,
    max_value=8,
    value=4
)


if st.button("生成回答"):
    if not question:
        st.warning("请先输入问题。")
    else:
        try:
            with st.spinner("正在从知识库中检索相关内容..."):
                docs = retrieve_docs(question, k=top_k)

            if has_relevant_docs(docs):
                with st.spinner("正在调用 Groq 大模型生成回答..."):
                    answer = generate_answer(question, docs)
            else:
                answer = REFUSAL_MESSAGE

            st.subheader("AI 回答")
            st.write(answer)

            st.subheader("参考片段")
            if not docs:
                st.warning("没有检索到相关内容。")
            else:
                for i, (doc, score) in enumerate(docs, start=1):
                    page = doc.metadata.get("page", "未知页码")
                    source = doc.metadata.get("source", "未知来源")
                    source_name = os.path.basename(source)

                    if isinstance(page, int):
                        page = page + 1

                    with st.expander(
                        f"参考片段 {i} | 来源：{source_name} | 页码：{page} | 距离分数：{score:.4f}"
                    ):
                        st.write(doc.page_content)
                        st.caption(
                            f"来源文件：{source_name} | 页码：{page} | 距离分数：{score:.4f}（越小越相关）"
                        )

        except Exception as e:
            st.error("生成回答失败。")
            st.write("错误原因：")
            st.code(str(e))
            st.warning(
                "请确认：1. 已上传 PDF 并建立知识库；2. GROQ_API_KEY 已正确写入 .env；3. 网络正常。"
            )


st.header("3. 当前项目说明")

st.info("""
当前版本已经升级为 RAG 问答系统：

PDF 文档 → 文本切分 → 本地向量化 → Chroma 向量数据库 → 用户问题检索 → Groq 大模型生成回答 → 展示参考片段

这个版本可以作为完整的 AI 应用项目写入简历。
""")
