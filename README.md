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

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的百炼 API Key
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

后端启动后访问 http://localhost:8000/api/health 确认服务状态。

### 3. 启动前端

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

## 演示数据

演示主题和用户画像位于 `data/demo/demo-data.json`，包含：

- **1 个演示主题**：免疫系统如何识别病毒
- **4 个场景配置**：科普传播、课堂教学、科研展示、长期学习陪伴
- **3 个演示用户**：高一学生、大学低年级学生、科研新手
