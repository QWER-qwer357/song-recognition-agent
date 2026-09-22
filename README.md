# 🎵 听歌识曲 AI Agent 系统

基于 FastAPI + LangGraph + RAG + 多Agent 的听歌识曲智能体系统。

## ✨ 核心功能
- 🎧 Shazam 式音频指纹提取与匹配
- 🗄️ MySQL 指纹库存储与毫秒级匹配
- 🧠 LangGraph 多 Agent 编排（识别/信息/推荐/对话）
- 📚 RAG 混合检索（Elasticsearch + BM25 + 向量 + RRF）
- 💾 短期与长期记忆系统（滑动窗口 + 动态摘要 + ChromaDB）
- ⚡ Kafka 异步任务处理（削峰填谷）
- 🛡️ 死循环检测、熔断器、幻觉防护、软删除审计
- 📊 Prometheus 监控与 Precision/Recall/F1 评估

## 🚀 一键启动
```bash
docker-compose up -d