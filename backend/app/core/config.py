"""
全局配置文件
从 .env 文件和环境变量中读取所有配置项
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()

# ── 阿里云百炼 API ──────────────────────────────────
# 百炼 API Key，用于调用大模型和嵌入模型
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "your-api-key-here")
# 百炼 OpenAI 兼容接口地址
DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
# 对话模型名称
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")
# 嵌入模型名称
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")
# 嵌入向量维度
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))

# ── 数据库 ──────────────────────────────────────────
# SQLite 数据库文件路径
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./data/app.db"
)
# 同步版数据库URL（用于建表等初始化操作）
DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    "sqlite:///./data/app.db"
)

# ── JWT 认证 ────────────────────────────────────────
# JWT 签名密钥（生产环境请更换为复杂随机字符串）
SECRET_KEY = os.getenv("SECRET_KEY", "langchain-rag-secret-key-change-in-production")
# 加密算法
ALGORITHM = "HS256"
# Token 过期时间（分钟），默认24小时
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# ── 管理员默认配置 ──────────────────────────────────
# 首次初始化时创建的管理员账号
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123456")

# ── 文件上传 ────────────────────────────────────────
# 上传文件存储目录
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
# 单个文件最大大小（字节），默认10MB
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))
# 允许上传的文件类型
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".csv", ".md", ".markdown", ".docx", ".doc"}

# ── 向量数据库 (ChromaDB) ──────────────────────────
# ChromaDB 数据存储路径
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
# 检索时返回的候选片段数量
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "6"))

# ── Redis 缓存 ──────────────────────────────────────
# Redis 连接地址（留空则不启用缓存）
REDIS_URL = os.getenv("REDIS_URL", "")

# ── RAG 参数 ────────────────────────────────────────
# 文本分割块大小
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
# 文本分割块重叠大小
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
# LLM 温度参数（0=精确，1=创造性）
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# ── 服务配置 ────────────────────────────────────────
# 后端服务端口
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
# 是否开启调试模式
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
