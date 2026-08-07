# 安全检查报告

**时间**：2026-08-01
**扫描范围**：backend/app/ + frontend/src/

## 总览

| 类别 | 发现数 | 严重度 |
|------|--------|--------|
| 硬编码敏感信息 | 0 | 🔴 |
| 注入漏洞 | 0 | 🔴 |
| 配置安全隐患 | 2 | 🟡 |

## 详细发现

### ✅ 已排除的误报

- `DASHSCOPE_API_KEY` — 从环境变量读取，默认值 `your-api-key-here` 是占位符，真实 Key 在 `.env` 中（已 gitignore）
- 所有 `password`/`token` 引用 — 均为变量名、函数参数、bcrypt 哈希处理，无明文硬编码
- 所有 `db.execute(select(...))` — 使用 SQLAlchemy ORM 参数化查询，无 SQL 字符串拼接

### 🟡 警告

| 文件:行号 | 类别 | 问题 | 建议 |
|-----------|------|------|------|
| config.py:40 | 弱密钥 | SECRET_KEY 默认值较弱 | 生产环境改为随机 32 位字符串 |
| config.py:99 | 调试模式 | DEBUG=true | 部署到生产环境时改为 false |

### ✅ 安全项确认

- bcrypt 密码哈希 ✅
- JWT Token 认证 ✅
- CORS 仅允许 localhost ✅
- .env 已加入 .gitignore ✅
- 无命令注入风险 ✅
- 无 SQL 注入风险 ✅

## 建议

1. 生产环境部署前，将 `SECRET_KEY` 改为强随机字符串
2. 生产环境将 `DEBUG` 设为 `false`
