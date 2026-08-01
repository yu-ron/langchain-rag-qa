# LangChain RAG 知识库问答系统

基于 LangChain 框架的企业级 RAG 知识库问答系统，面向电商平台商品知识问答场景。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python FastAPI |
| 前端框架 | Vue 3 + Element Plus |
| 大模型 | 阿里云百炼 (qwen-plus) |
| 嵌入模型 | text-embedding-v4 (1024维) |
| 向量数据库 | ChromaDB |
| 关系数据库 | SQLite |
| AI 框架 | LangChain |

## 快速开始

### 1. 配置环境
```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 DASHSCOPE_API_KEY
```

### 2. 初始化数据库
```bash
cd backend
python init_db.py
# 创建管理员账号：admin / 123456
```

### 3. 启动后端
```bash
cd backend
python main.py
# http://localhost:8000
```

### 4. 启动前端（新窗口）
```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

## 功能

- 用户注册/登录，JWT 认证
- 知识库管理（上传 PDF/TXT/CSV/DOCX/Markdown）
- 流式 RAG 问答，引用溯源
- 多用户多会话管理
- 混合检索（向量 + BM25 关键词）
- 对话导出 Markdown
- API 限流

## 管理员

默认账号：`admin` / `123456`
