# 🎵 Song Finder · 听歌识曲 AI Agent 系统

基于 **FastAPI + LangGraph** 的听歌识曲智能体系统：上传一段音频，自动提取音频指纹并在曲库中匹配识别；结合大语言模型实现多 Agent 意图路由与多轮对话，支持自然语言查歌、歌曲信息查询与相似推荐。曲库 193 首，识别准确率 90%，平均响应 2.1s。

## 📖 项目简介

仿 Shazam 原理的完整落地项目，覆盖「音频处理 → 指纹生成 → 数据库匹配 → 多 Agent 对话 → Docker 部署」全链路。适合作为 Python 后端 + AI Agent 应用开发的入门级完整项目。

## ✅ 核心链路（主流程）

- 🎧 **Shazam 式音频指纹识别**：librosa 频谱分析 → 峰值提取 → 哈希指纹生成，MySQL 存储 + SQL IN 批量匹配，匹配阈值优化（10 → 50）防止噪音误识别
- 🧠 **LangGraph 多 Agent 编排**：意图分类（识别 / 查信息 / 推荐 / 闲聊）→ 路由到专业子 Agent → 结果汇总，通过 `thread_id` 实现多轮对话记忆
- 🐳 **Docker Compose 一键部署**：6 个容器编排（API + Worker + MySQL + Redis + Kafka + Elasticsearch）
- 🖥️ **Web 前端页面**：暗黑毛玻璃风格 UI，含「小皮卡」AI 助手（皮卡丘头像），识别成功后自动解锁对话并注入歌曲上下文

## 🔧 扩展模块（已实现，用于学习对应技术）

- 📚 RAG 混合检索（BM25 + 向量检索 + RRF 融合）
- 💾 记忆系统（短期滑动窗口 + 长期动态摘要）
- 🔌 MCP 工具服务（标准化外部能力封装）
- ⚡ Kafka 异步任务处理（confluent-kafka 客户端）
- 🛡️ 可靠性保障（死循环检测、熔断器、输出校验）
- 📊 Prometheus 监控与评估指标（Precision / Recall / F1）

## 🧰 技术栈

| 分类 | 技术 |
|------|------|
| 语言 | Python 3.11 |
| Web 框架 | FastAPI + Uvicorn |
| 数据库 | MySQL 8.0（SQLAlchemy + PyMySQL） |
| AI 编排 | LangGraph（多 Agent + 意图路由 + MemorySaver） |
| 大模型 | 智谱 GLM-4-Plus（兼容 OpenAI 接口） |
| 音频处理 | librosa、NumPy、SciPy、pydub |
| 检索（扩展） | Elasticsearch、Sentence-Transformers |
| 缓存 / 消息（扩展） | Redis、Kafka（confluent-kafka） |
| 向量库（扩展） | ChromaDB |
| 部署 | Docker、Docker Compose |

## 🚀 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/QWER-qwer357/song-recognition-agent.git
cd song-recognition-agent

# 2. 配置 LLM API Key
# 编辑以下 4 个文件，把 api_key="xxx" 换成你的智谱 Key：
#   src/agents/orchestrator.py
#   src/agents/memory.py
#   src/agents/graph_agent.py
#   src/agents/recognizer_agent.py

# 3. 一键启动全部服务（6 个容器）
docker-compose up -d

# 4. 准备曲库：把 mp3 / flac / wav 音乐文件放入
#   data/library/raw/

# 5. 批量导入曲库（激活 Python 3.11 环境后执行）
conda activate langchain1.2
python src/utils/batch_import.py

# 6. 打开前端页面
# 浏览器访问 http://localhost:8010/ui
``` 

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/` | 健康检查 |
| GET  | `/ui` | Web 前端页面 |
| POST | `/fingerprint` | 上传歌曲文件，提取指纹入库（建立曲库） |
| POST | `/recognize` | 上传音频片段，提交异步识别任务，返回 `session_id` |
| GET  | `/result/{session_id}` | 轮询识别结果（异步任务） |
| POST | `/chat` | 多轮对话接口，Agent 自动识别意图并调用工具 |

交互式 API 文档：启动后访问 `http://localhost:8010/docs`（FastAPI 自动生成 Swagger）。

## 📁 项目结构
``` 
song-recognition-agent/
├── docker-compose.yml          # 多容器编排（6 个服务）
├── Dockerfile                  # API / Worker 服务镜像
├── requirements.txt            # Python 依赖
├── static/
│   └── index.html              # Web 前端页面（含小皮卡助手）
├── data/
│   └── library/
│       ├── raw/                # 原始音乐文件（用户自行放入）
│       └── mp3/                # 批量导入后自动转码的 mp3
└── src/
    ├── agents/
    │   ├── orchestrator.py     # 多 Agent 编排（意图分类 + 路由 + 汇总）
    │   ├── graph_agent.py      # LangGraph 图构建
    │   ├── recognizer_agent.py # 识别子 Agent
    │   └── memory.py           # 记忆系统（扩展模块）
    ├── api/
    │   └── server.py           # FastAPI 接口层
    ├── db/
    │   ├── database.py         # 数据库连接与建表
    │   └── matcher.py          # 指纹匹配逻辑（阈值=50）
    ├── mcp/
    │   └── music_server.py     # MCP 工具服务（扩展模块）
    └── utils/
        ├── fingerprint.py      # 音频指纹提取（核心算法）
        ├── audio_processor.py  # 音频预处理与可视化
        ├── batch_import.py     # 曲库批量导入（自动解析歌手/歌名）
        ├── rag.py              # RAG 混合检索（扩展模块）
        ├── kafka_processor.py  # Kafka 异步处理（扩展模块）
        ├── cache.py            # Redis 缓存（扩展模块）
        ├── metrics.py          # Prometheus 监控（扩展模块）
        ├── evaluator.py        # 评估器（扩展模块）
        └── safety.py           # 可靠性保障（扩展模块）
```

## ✨ 技术亮点

1. **指纹抗噪设计**：采用「锚点 + 配对峰 + 时间差」三元组哈希，噪音难以同时掩盖两个强峰值；匹配阈值从 10 优化到 50，显著减少短音频误匹配
2. **多 Agent 兜底路由**：意图分类失败自动降级到闲聊 Agent，子 Agent 异常返回友好提示，全链路无裸奔报错
3. **上下文感知对话**：前端识别成功后自动解锁聊天框，并将当前歌曲名注入 `/chat` 请求，Agent 通过 `MemorySaver` + `thread_id` 实现多轮记忆，不会出现「哪首歌？」的尴尬反问
4. **工程化闭环**：从音频上传 → Kafka 异步 → Worker 消费 → Redis 缓存 → 前端轮询的完整链路，`docker-compose up -d` 一条命令拉起全部服务
5. **跨平台踩坑沉淀**：解决过 `kafka-python` 在 Windows 下的消费者假死（改用 `confluent-kafka`）、`depends_on` 只保证启动顺序不保证服务就绪、`docker-compose down -v` 误删数据卷等问题

## 📝 说明

本项目为个人学习型全栈项目，**核心链路**（指纹识别 / 多 Agent 对话 / Docker 部署 / 前端交互）为完整业务主流程；标注「**扩展模块**」的部分为围绕主项目学习相关技术的实践，用于验证不同技术方案的落地方式。

---

⭐ 如果这个项目对你有帮助，欢迎 Star 交流！   