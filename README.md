# 知己科教 Agent

一个能记住用户认知特点、严格锁定科学事实、把专业知识讲得像真人老师一样的科教智能体。

**主演示主题：免疫系统如何识别病毒**

## 项目结构

```
science-agent/
├── frontend/          # 前端 (Vite + React)
├── backend/           # 后端 (Python FastAPI)
├── data/              # 数据目录
│   ├── knowledge/     #   知识库文件
│   ├── eval/          #   评估数据集
│   └── demo/          #   演示数据
├── docs/              # 文档
├── finetune/          # 微调相关
│   ├── datasets/      #   微调数据集
│   ├── scripts/       #   微调脚本
│   └── reports/       #   微调报告
├── screenshots/       # 百炼控制台截图
├── .env.example       # 环境变量模板
└── README.md
```

## 环境要求

- Python >= 3.10
- Node.js >= 18

## 快速启动

### 1. 获取百炼 API Key

本项目使用阿里云百炼平台提供的千问（Qwen）模型。你需要：

1. 登录 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 开通模型服务（推荐 qwen-plus 或 qwen-turbo）
3. 在控制台右上角「API-KEY 管理」创建 API Key
4. **保存百炼控制台截图**到 `screenshots/` 目录（包含模型列表和 API Key 管理页，用于赛事交付材料）

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，将 your_api_key_here 替换为你的百炼 API Key
```

`.env` 文件内容：

```ini
DASHSCOPE_API_KEY=你的百炼APIKey
QWEN_MODEL=qwen-plus
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

后端启动后访问 http://localhost:8000/api/health 确认服务状态。
- `llm_ready: true` 表示 LLMClient 已成功初始化
- `llm_ready: false` 表示 API Key 未配置，需检查 `.env` 文件

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端启动后访问 http://localhost:5173 查看首页。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 服务健康检查 |
| GET | `/api/llm/status` | LLMClient 状态与调用日志 |
| GET | `/api/scenarios` | 场景列表 |
| POST | `/api/chat` | 对话接口 |
| POST | `/api/knowledge/upload` | 上传知识资料（.txt / .md） |
| GET | `/api/knowledge/documents` | 已上传资料列表 |
| GET | `/api/knowledge/documents/{id}` | 文档详情与切片 |

## 演示数据

演示主题和用户画像位于 `data/demo/demo-data.json`，包含：

- **1 个演示主题**：免疫系统如何识别病毒
- **4 个场景配置**：科普传播、课堂教学、科研展示、长期学习陪伴
- **3 个演示用户**：高一学生、大学低年级学生、科研新手
