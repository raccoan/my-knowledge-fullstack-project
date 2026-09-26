# AI 驱动的个人知识库与智能学习平台

一个面向开发者学习与知识管理场景的 AI 全栈应用。

项目基于 **Vue 3 + TypeScript + FastAPI + MySQL + Chroma + LLM** 构建，围绕个人知识管理、RAG 智能问答、简历解析以及 AI 模拟面试等场景，实现从资料管理到 AI 学习辅助的完整流程。

> 本项目为个人学习与项目实践作品，当前以本地开发方式运行。

---

## 📌 项目介绍

本项目并非单纯的 AI Chat Demo，而是一个面向开发者学习场景的 AI 知识管理与学习辅助平台。

用户可以将自己的学习资料、简历等内容导入系统，由 AI 对内容进行解析，并结合个人知识库完成智能问答和模拟面试。

核心流程：

```text
个人资料
    ↓
知识库
    ↓
文档解析
    ↓
文本切分
    ↓
向量化
    ↓
向量检索
    ↓
LLM
    ↓
AI 回答
```

AI 模拟面试流程：

```text
上传简历
    ↓
AI 解析简历
    ↓
提取项目 / 技术栈 / 经历
    ↓
生成针对性面试问题
    ↓
用户回答
    ↓
AI 追问
    ↓
AI 评分
    ↓
回答反馈 / 参考答案 / 薄弱知识点
```

---

# ✨ 主要功能

## 1. 用户系统

* 用户注册
* 用户登录
* JWT 身份认证
* 邮箱验证码
* 忘记密码
* 密码重置
* 登录状态管理
* 用户信息隔离

---

## 2. 个人知识库

* PDF 文件上传
* 文件列表
* 文件删除
* PDF 文本解析
* 文本切分
* 文档状态管理
* 文档详情查看
* 知识片段查看

文档上传后会经过：

```text
PDF
 ↓
文本解析
 ↓
文本切分
 ↓
Embedding
 ↓
Chroma
```

最终建立可供检索的个人知识库。

---

## 3. RAG 智能问答

系统基于用户自己的知识库进行检索增强生成。

主要流程：

```text
用户问题
    ↓
问题向量化
    ↓
Chroma 向量检索
    ↓
获取相关知识片段
    ↓
构建 Prompt
    ↓
LLM
    ↓
生成回答
```

不同用户的知识库数据通过 `user_id` 进行隔离。

---

## 4. AI 对话

* 创建新对话
* 历史对话列表
* 对话消息持久化
* 删除对话
* 修改对话标题
* AI 流式输出
* Markdown 内容展示

AI 回答采用流式响应，前端可以逐步显示模型生成的内容。

---

## 5. AI 简历解析

* 上传 PDF 简历
* 自动提取简历文本
* AI 解析简历
* 提取项目经历
* 提取技术栈
* 提取实习经历
* 提取教育经历
* 保存结构化简历数据

---

## 6. AI 模拟面试

模拟面试模块结合用户简历与知识库内容，生成针对性的技术面试。

主要功能：

* 根据简历生成面试问题
* 多轮面试
* 根据用户回答进行 AI 追问
* AI 评价回答
* 回答评分
* 回答反馈
* 参考答案
* 知识薄弱点分析
* 面试记录持久化
* 面试结果报告

面试回答分析主要关注：

```text
用户当前回答
+
用户简历
+
个人知识库
        ↓
AI 分析
        ↓
评分
+
回答反馈
+
参考答案
+
知识薄弱点
```

---

# 🛠️ 技术栈

## 前端

* Vue 3
* TypeScript
* Vite
* Pinia
* Vue Router
* Ant Design Vue
* Axios

## 后端

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* PyMySQL
* python-jose
* bcrypt

## AI / RAG

* LLM API
* Embedding
* Chroma
* RAG
* PDF 文本解析
* 文本切分

## 数据库

* MySQL 8

## 开发工具

* Git
* GitHub
* PyCharm
* VS Code
* Navicat

---

# 📂 项目结构

```text
my-knowledge-fullstack-project/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── file.py
│   │   ├── document.py
│   │   ├── chunk.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── resume.py
│   │   ├── interview.py
│   │   └── interview_message.py
│   │
│   ├── routers/
│   │   ├── users.py
│   │   ├── files.py
│   │   ├── chat.py
│   │   ├── conversations.py
│   │   ├── resumes.py
│   │   └── interviews.py
│   │
│   ├── schemas/
│   │   ├── user.py
│   │   ├── chat.py
│   │   ├── resume.py
│   │   └── interview.py
│   │
│   ├── utils/
│   │   ├── auth.py
│   │   ├── jwt.py
│   │   ├── password.py
│   │   ├── pdf.py
│   │   ├── splitter.py
│   │   ├── embedding.py
│   │   ├── vector.py
│   │   ├── llm.py
│   │   └── rag.py
│   │
│   ├── sql/
│   │   └── init.sql
│   │
│   ├── requirements.txt
│   ├── .env
│   ├── .env.example
│   ├── uploads/
│   └── chroma/
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── router/
│   │   ├── stores/
│   │   └── views/
│   │
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── .gitignore
└── README.md
```

### 本地运行产生的目录

以下内容不会提交到 GitHub：

```text
.venv/
backend/.env
backend/uploads/
backend/chroma/
frontend/node_modules/
frontend/dist/
```

---

# 🚀 本地运行

## 1. 克隆项目

确保电脑已经安装 Git。

执行：

```bash
git clone https://github.com/raccoan/my-knowledge-fullstack-project.git
```

进入项目：

```bash
cd my-knowledge-fullstack-project
```

---

# 2. 环境要求

建议准备以下环境：

* Python 3.10+
* Node.js 18+
* MySQL 8.0+
* Git

检查版本：

```bash
python --version
node --version
npm --version
mysql --version
git --version
```

---

# 3. 创建 MySQL 数据库

打开 MySQL / Navicat，创建数据库：

```sql
CREATE DATABASE fastapi_demo
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;
```

然后进入：

```text
backend/sql/init.sql
```

执行该 SQL 文件。

执行完成后，会创建项目所需的数据表：

```text
users
files
documents
chunks
conversations
messages
resumes
interviews
interview_messages
verification_codes
```

> `init.sql` 只包含数据库表结构，不包含项目原有测试数据。

---

# 4. 配置后端环境

进入后端目录：

```bash
cd backend
```

如果本地没有 Python 虚拟环境，可以创建：

### Windows

```powershell
python -m venv .venv
```

激活：

```powershell
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

# 5. 安装 Python 依赖

确保当前位于：

```text
my-knowledge-fullstack-project/backend
```

执行：

```bash
pip install -r requirements.txt
```

---

# 6. 配置 `.env`

项目使用环境变量保存数据库连接、JWT 密钥以及 AI / 邮箱相关配置。

进入：

```text
backend/
```

复制：

```text
.env.example
```

创建：

```text
.env
```

最终结构：

```text
backend/
├── .env
└── .env.example
```

然后根据自己的环境修改 `.env`。

示例：

```env
DATABASE_URL=mysql+pymysql://用户名:密码@localhost:3306/fastapi_demo

SECRET_KEY=your_secret_key
```

如果项目需要使用 AI 和邮箱验证码功能，还需要按照 `.env.example` 中的字段配置对应的 API Key、SMTP 等信息。

> `.env` 包含敏感信息，已经加入 `.gitignore`，不要提交到 GitHub。

---

# 7. 启动后端

确保当前目录：

```text
my-knowledge-fullstack-project/backend
```

执行：

```bash
uvicorn main:app --reload
```

启动成功后：

```text
http://127.0.0.1:8000
```

可以访问后端。

FastAPI 自动生成的接口文档：

```text
http://127.0.0.1:8000/docs
```

打开 `/docs` 可以查看和测试后端 API。

---

# 8. 启动前端

重新打开一个终端。

进入项目根目录：

```bash
cd my-knowledge-fullstack-project
```

进入前端：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动：

```bash
npm run dev
```

启动成功后，终端会显示类似：

```text
Local: http://localhost:5173/
```

浏览器访问：

```text
http://localhost:5173
```

即可进入项目。

---

# 🔗 前后端运行关系

本地开发环境：

```text
                    ┌───────────────┐
                    │    浏览器      │
                    │ localhost:5173│
                    └───────┬───────┘
                            │
                            ↓
                    ┌───────────────┐
                    │   Vue 3 前端   │
                    └───────┬───────┘
                            │
                       HTTP / SSE
                            │
                            ↓
                    ┌───────────────┐
                    │ FastAPI 后端   │
                    │ localhost:8000│
                    └───────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
        ┌─────────┐    ┌─────────┐    ┌─────────┐
        │  MySQL  │    │ Chroma  │    │   LLM   │
        └─────────┘    └─────────┘    └─────────┘
```

---

# 🔐 数据与配置说明

## `.env`

用于保存：

* MySQL 数据库连接信息
* JWT 密钥
* LLM API Key
* SMTP 配置

不会提交到 GitHub。

---

## `.env.example`

用于说明项目需要哪些环境变量。

会提交到 GitHub。

---

## `.venv`

Python 虚拟环境，仅用于本地开发。

不会提交到 GitHub。

如果重新 clone 项目，需要自行创建。

---

## `uploads/`

用户上传的 PDF、简历等本地文件会保存到该目录。

不会提交到 GitHub。

---

## `chroma/`

Chroma 在本地运行时产生的向量数据库数据。

不会提交到 GitHub。

---

# 🧠 核心技术实现

## 1. RAG

项目通过以下流程实现个人知识库问答：

```text
PDF 文件
   ↓
文本解析
   ↓
文本切分
   ↓
Embedding
   ↓
Chroma 向量数据库
   ↓
相似度检索
   ↓
获取相关知识片段
   ↓
构建 Prompt
   ↓
LLM
   ↓
生成回答
```

检索过程中会结合当前登录用户的 `user_id` 对知识进行隔离。

---

## 2. SSE 流式响应

AI Chat 使用流式响应。

后端持续向前端返回模型生成的内容：

```text
LLM
 ↓
数据片段
 ↓
SSE
 ↓
Vue 前端
 ↓
逐步显示回答
```

从而实现类似 ChatGPT 的流式回答效果。

---

## 3. JWT 身份认证

用户登录成功后：

```text
用户名 + 密码
       ↓
后端验证
       ↓
生成 JWT
       ↓
前端保存 Token
       ↓
后续请求携带 Token
       ↓
后端验证用户身份
```

知识库、对话、简历和面试等功能都会根据当前用户身份进行数据隔离。

---

## 4. AI 简历解析

用户上传 PDF 简历后：

```text
PDF 简历
   ↓
文本提取
   ↓
LLM
   ↓
结构化简历数据
```

用于后续 AI 模拟面试。

---

## 5. AI 模拟面试

AI 模拟面试结合：

```text
用户简历
+
用户知识库
+
当前回答
```

动态生成后续问题，并对用户回答进行分析。

最终保存：

```text
回答
评分
反馈
参考答案
知识薄弱点
```

---

# 📸 项目页面

## AI 对话

在这里放 Chat 页面截图。

## 个人知识库

在这里放知识库页面截图。

## 文档详情

在这里放文档详情页面截图。

## AI 简历解析

在这里放简历解析页面截图。

## AI 模拟面试

在这里放模拟面试页面截图。

## 面试结果

在这里放面试评价和分析页面截图。

> 后续可以将项目实际截图放到 `README.md` 中，用于展示项目效果。

---

# 📌 项目地址

GitHub：

https://github.com/raccoan/my-knowledge-fullstack-project

---

# 📄 License

本项目主要用于个人学习、技术实践以及项目展示。
