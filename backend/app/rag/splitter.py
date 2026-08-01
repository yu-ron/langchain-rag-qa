"""
文本分割器
把长文档切成小块（chunk），方便后续检索
"""
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP


def split_documents(documents: List[Document]) -> List[Document]:
    """
    把文档列表切分成更小的片段

    为什么要切分？
    - 大模型一次能读的内容有限（上下文窗口）
    - 小块更容易精确检索到相关信息
    - 500 字一块，相邻两块重叠 50 字，防止一句话被切断

    比如：
    "iPhone 15 支持 5G 网络，搭载 A16 芯片，屏幕尺寸..."
    →
    ["iPhone 15 支持 5G 网络，搭载 A16 芯片...",
     "A16 芯片，屏幕尺寸..."]
    （重叠部分保证 "A16 芯片" 不会丢失）
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,        # 每块最多多少个字符
        chunk_overlap=CHUNK_OVERLAP,  # 相邻两块重叠多少个字符
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        # 按上面的分隔符顺序递归切分：先按段落，再按句子，最后按字符
    )

    chunks = text_splitter.split_documents(documents)

    # 给每个 chunk 标上序号
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    return chunks
