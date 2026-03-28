# AI 智能简历分析系统

一个面向招聘场景的智能简历分析项目，支持上传 PDF 简历、解析文本、提取关键信息、结合岗位描述生成匹配评分，并通过中文界面展示结构化结果。项目采用前后端分离设计，后端使用 Python + FastAPI，前端为可直接部署到 GitHub Pages 的静态页面，兼容阿里云函数计算 Web 函数部署方式。

## 1. 项目目标

在招聘流程中，HR 或面试官往往需要快速处理大量简历。本项目聚焦以下目标：

- 自动解析上传的 PDF 简历
- 提取姓名、电话、邮箱、教育背景、项目经历、技能等核心信息
- 接收岗位需求描述并进行关键词分析
- 计算简历与岗位之间的匹配评分
- 以清晰、可展示的方式返回分析结果

## 2. 功能概览

### 2.1 简历上传与解析

- 支持上传单个 PDF 简历
- 支持多页 PDF 文本解析
- 对提取内容进行基础清洗
- 对扫描版或图片型 PDF 给出明确提示

### 2.2 关键信息提取

- 必选字段：姓名、电话、邮箱、地址
- 加分字段：求职意向、期望薪资、工作年限、教育背景、项目经历、技能标签
- 支持两种提取模式：
  - `LLM` 模式：调用 DeepSeek 接口做结构化抽取
  - `Heuristic` 模式：未配置大模型时使用正则和启发式规则回退

### 2.3 岗位匹配与评分

- 对岗位描述进行关键词分析
- 结合简历内容计算：
  - 技能匹配率
  - 经验相关性
  - 教育背景得分
  - 综合匹配评分
- 输出中文评分说明，便于业务人员直接理解

### 2.4 缓存机制

- 优先使用 Redis 作为缓存
- 未配置 Redis 时自动退化为内存缓存
- 对相同简历和相同岗位描述的分析结果进行复用，减少重复计算

### 2.5 前端展示

- 提供简洁精致的中文展示页面
- 默认优先展示业务结果
- “原始 JSON” 折叠隐藏，按需展开调试
- 适合直接演示给评审团队或面试官

## 3. 项目架构

项目采用前后端分离结构：

```text
AIResime/
├── app/
│   ├── api/                # 路由层
│   ├── core/               # 配置与缓存
│   ├── models/             # Pydantic 数据模型
│   ├── services/           # PDF解析、LLM调用、匹配评分等业务逻辑
│   └── utils/              # 文本清洗、关键词等工具函数
├── frontend/               # 前端源码
├── docs/                   # GitHub Pages 发布目录
├── tests/                  # 测试
├── app.py                  # 函数计算 / 本地统一启动入口
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量示例
└── README.md
```

### 3.1 后端分层说明

- `api`：接收 HTTP 请求，做参数校验和响应封装
- `services`：实现核心业务逻辑
- `models`：统一管理输入输出结构
- `core`：环境配置、缓存客户端
- `utils`：文本清洗、关键词提取、哈希计算

### 3.2 核心流程

```text
上传 PDF
   ↓
PDF 解析与文本清洗
   ↓
简历信息提取（LLM / 规则）
   ↓
岗位描述关键词分析
   ↓
匹配评分计算
   ↓
缓存结果
   ↓
前端展示结构化信息和评分说明
```

## 4. 技术选型

### 后端

- `FastAPI`
  - 轻量、性能好、适合构建 RESTful API
  - 自带参数校验和文档能力
- `pypdf`
  - 用于解析 PDF 文本内容
- `Pydantic`
  - 统一数据结构与返回格式
- `Redis`
  - 用于缓存解析和评分结果
- `httpx`
  - 调用 DeepSeek 大模型接口

### AI 能力

- 默认接入 `DeepSeek Chat Completions`
- 提供中文评分说明
- 对返回格式不稳定的数据做了兼容处理
- 当模型返回英文说明时，后端会自动翻译为中文再输出

### 前端

- 原生 `HTML + CSS + JavaScript`
- 零依赖，部署简单
- 适合快速托管到 GitHub Pages / 静态站点服务

## 5. API 说明

### 5.1 健康检查

`GET /api/v1/health`

返回示例：

```json
{
  "status": "ok"
}
```

### 5.2 简历分析接口

`POST /api/v1/resumes/analyze`

请求方式：

- `multipart/form-data`

请求字段：

- `file`：PDF 文件，必填
- `job_description`：岗位描述，必填于评分场景

返回内容包含：

- 简历基础信息
- 教育背景、项目经历、技能标签
- 岗位关键词分析
- 匹配评分
- 评分说明
- 缓存命中标识

### 5.3 仅做岗位匹配接口

`POST /api/v1/jobs/match`

请求体支持：

- `resume_text`
- `cleaned_resume_text`
- `extracted`
- `job_description`

适用于已完成简历解析后，重复计算不同岗位的匹配结果。

## 6. 环境变量说明

复制 `.env.example` 为 `.env`，然后按需填写。

常用变量：

- `APP_ENV`：运行环境
- `APP_HOST`：服务监听地址
- `APP_PORT`：服务端口
- `REDIS_URL`：Redis 连接地址，可选
- `LLM_API_KEY`：DeepSeek API Key
- `LLM_API_URL`：DeepSeek Chat Completions 地址
- `LLM_MODEL`：模型名，默认 `deepseek-chat`

## 7. 本地运行方式

### 7.1 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 7.2 启动后端

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

或使用统一入口：

```bash
python app.py
```

### 7.3 打开前端

可直接访问：

- `frontend/index.html` 本地调试
- 或通过 `docs/` 目录配合静态服务器访问

如果后端地址不是 `http://127.0.0.1:8000`，可以：

- 使用 `config.js` 指定 API 地址
- 或在访问页面时通过 `?api=http://your-api-domain` 指定后端地址

## 8. 部署方式

### 8.1 Docker 部署

如果你的前端已经部署完成，推荐只把当前后端项目放到 Linux 服务器上，通过 Docker 启动。

项目已经提供：

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

部署步骤：

1. 上传项目后端代码到 Linux 服务器
2. 准备 `.env`
3. 执行 Docker Compose 启动

#### 1. 准备 `.env`

```bash
cp .env.example .env
```

编辑 `.env`，至少填写：

```env
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=["https://你的-github-pages-域名"]

LLM_API_KEY=你的DeepSeekKey
LLM_API_URL=https://api.deepseek.com/v1/chat/completions
LLM_MODEL=deepseek-chat
```

如果你需要 Redis，可以额外补充：

```env
REDIS_URL=redis://你的redis地址:6379/0
```

#### 2. 构建并启动

```bash
docker compose up -d --build
```

#### 3. 查看运行状态

```bash
docker compose ps
docker compose logs -f
```

#### 4. 验证接口

```bash
curl http://127.0.0.1:8000/api/v1/health
```

如果返回：

```json
{"status":"ok"}
```

说明后端启动成功。

#### 5. 停止服务

```bash
docker compose down
```

如果更新代码后重新部署：

```bash
docker compose up -d --build
```

#### 6. 对外访问建议

如果前端已经在 GitHub Pages 上线，建议后端再配一层 Nginx：

- 用域名访问后端 API
- 统一走 `80/443`
- 配置 HTTPS
- 反向代理到容器的 `8000` 端口

### 8.2 阿里云函数计算部署

项目已提供 `app.py` 作为统一启动入口，适合部署为阿里云函数计算 Web 函数。

建议部署方式：

1. 创建 Python Web 函数
2. 上传项目代码和依赖
3. 启动命令设置为：

```bash
python app.py
```

4. 监听端口设置为：

```text
9000
```

5. 在环境变量中配置：

- `LLM_API_KEY`
- `LLM_API_URL`
- `LLM_MODEL`
- `REDIS_URL`

参考官方文档：

- [阿里云函数计算 Web 函数快速入门](https://help.aliyun.com/zh/functioncompute/fc/web-function-quick-start)
- [阿里云函数计算 Custom Runtime 文档](https://help.aliyun.com/zh/functioncompute/fc-2-0/user-guide/custom-runtime/)

### 8.3 前端部署到 GitHub Pages

项目已经额外提供 `docs/` 目录，适合直接用于 GitHub Pages 发布。

推荐步骤：

1. 推送代码到 GitHub
2. 在仓库设置中启用 GitHub Pages
3. 选择主分支的 `docs/` 目录作为发布源
4. 确保前端能够访问后端 API

## 9. 使用说明

### 页面使用步骤

1. 打开前端页面
2. 上传一份 PDF 简历
3. 输入岗位需求描述
4. 点击“开始分析”
5. 查看：
   - 综合评分
   - 技能匹配率、经验相关性、教育背景得分
   - 结构化候选人信息
   - 中文评分说明
   - 原始 JSON（按需展开）

### 结果说明

- 如果 PDF 可提取文本，系统会自动解析
- 如果 PDF 为图片型简历，会提示需要 OCR
- 如果配置了 DeepSeek，优先走 AI 抽取和 AI 评分
- 如果未配置大模型，仍可使用规则回退完成基础功能演示

## 10. 测试方式

执行：

```bash
pytest
```

当前测试覆盖：

- 匹配评分逻辑
- `multipart/form-data` 形式上传时岗位描述字段能正确传入并触发评分

## 11. 项目亮点

- 支持 AI 抽取与规则回退双模式
- 支持中文评分说明输出
- 支持 Redis / 内存双缓存策略
- 前端为可直接演示的中文页面
- 兼容本地运行、静态托管和函数计算部署

## 12. 已知限制

- 当前不支持 OCR，因此扫描版 PDF 无法提取文本
- 简历解析仍依赖 PDF 中存在可提取文本层
- 评分逻辑目前以关键词和规则为主，未来可升级为向量检索或更复杂的排序模型

## 13. 后续可扩展方向

- OCR 支持扫描版简历
- 批量简历分析与异步任务队列
- 向量检索增强岗位匹配
- 用户鉴权与管理后台
- 多岗位对比分析与候选人排名

## 14. 交付建议

提交给面试官时建议同时提供：

- GitHub 仓库地址
- 前端演示地址
- 后端演示地址
- 姓名与联系方式

---

如果你接下来需要，我还可以继续帮你补两样常见交付物：

- `LICENSE`
- 一份更适合面试官快速浏览的“项目亮点摘要版” README 开头
