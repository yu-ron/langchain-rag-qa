# LangChain RAG 企业级知识库问答系统

基于 LangChain 框架的企业级 RAG（检索增强生成）知识库问答系统，面向电商商品知识问答场景。支持多用户多会话、知识库管理、引用溯源和流式回答。

> 🌐 **在线演示**：http://42.121.121.9 （管理员：admin / 123456）

## ✨ 核心特性

- **RAG 全链路**：文档解析（PDF/Word/CSV/Markdown/TXT）→ 文本分割 → Embedding 向量化 → 混合检索 → LLM 流式生成
- **混合检索引擎**：向量语义检索 + BM25 关键词检索 + RRF 融合排序，比纯向量检索更精准
- **引用溯源**：AI 回答标注 `[来源N]`，点击即可查看知识库原文，解决大模型"幻觉"问题
- **多用户系统**：JWT 认证、角色权限（管理员/普通用户）、多会话管理、历史对话永久保存
- **流式输出**：SSE 流式推送，像 ChatGPT 一样逐字显示

## 🏗️ 系统架构

```
浏览器（Vue 3 前端）
    │  HTTP + SSE 流式
    ▼
FastAPI 后端
    ├── 认证模块（JWT + bcrypt）
    ├── 知识库管理（文档上传/解析/向量化）
    ├── RAG 问答（混合检索 + LLM 生成）
    ├── 会话管理（多会话/历史记录）
    │
    ├── LangChain 管道
    │   └── 加载 → 分割 → 嵌入 → ChromaDB → 检索 → 生成
    │
    ├── SQLite（用户/会话/消息）
    └── ChromaDB（知识库向量）
```

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python · FastAPI · LangChain |
| 大模型 | 阿里云百炼 qwen-plus |
| 嵌入模型 | text-embedding-v4（1024维） |
| 向量库 | ChromaDB |
| 数据库 | SQLite + SQLAlchemy |
| 前端 | Vue 3 + Element Plus + Pinia |
| 部署 | 阿里云 ECS + Nginx + systemd |

## 📊 性能数据

| 指标 | 数值 |
|------|------|
| 100 并发压测失败率 | 0.08% |
| 平均响应时间 | 160ms |
| 吞吐量 | 22 RPS |
| 单元测试 | 34 个用例全通过 |

## 🚀 快速开始

### 1. 配置环境

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 DASHSCOPE_API_KEY
```

### 2. 初始化数据库

```bash
python init_db.py
# 自动创建管理员账号 admin / 123456
```

### 3. 启动后端

```bash
python main.py
# http://localhost:8000（API 文档 /docs）
```

### 4. 启动前端（开发模式）

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

## 🧪 运行测试

```bash
cd backend
python -m pytest tests/ -v
```

## 📁 项目结构

```
├── backend/                 # Python 后端
│   ├── app/
│   │   ├── api/            # API 路由（auth/knowledge/chat/session/export）
│   │   ├── core/           # 配置、数据库、安全
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── services/       # 业务逻辑层
│   │   ├── rag/            # RAG 管道（loader/splitter/embeddings/retriever/chain）
│   │   └── utils/          # 工具（依赖注入/限流）
│   ├── tests/              # 34 个 pytest 测试用例
│   └── main.py             # 入口
└── frontend/               # Vue 3 前端
    └── src/
        ├── views/          # 登录/注册/问答/知识库/个人中心
        ├── stores/         # Pinia 状态管理
        └── api/            # Axios 请求封装
```

## 📝 压测

```bash
# 1. 创建 100 个测试账号
python tests/create_test_users.py

# 2. Mock 模式启动（不调真实 LLM API）
MOCK_LLM=true python main.py

# 3. 运行 Locust 压测
locust -f tests/locustfile.py --host=http://localhost:8000
```
