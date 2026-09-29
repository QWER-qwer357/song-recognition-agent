import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="glm-4-plus",
    temperature=0.7,
    api_key="xxx",  # 👈 替换成你真实的智谱 Key
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)


class MultiAgentState(TypedDict):
    user_input: str
    intent: str
    song_name: str
    recognize_result: str
    info_result: str
    recommend_result: str
    final_answer: str


def classify_intent(state: MultiAgentState):
    song = state.get("song_name", "")
    hint = f"【当前正在聊的歌曲是《{song}》】" if song else ""
    prompt = f"""判断用户意图，只返回一个词：
- recognize: 识别歌曲
- info: 查询歌曲信息、歌手、创作背景、故事
- recommend: 推荐相似风格的歌
- chat: 闲聊

{hint}
用户说："{state['user_input']}"
意图："""
    intent = llm.invoke(prompt).content.strip().lower()
    # 兜底：确保只返回合法意图
    if intent not in ["recognize", "info", "recommend", "chat"]:
        intent = "chat"
    print(f"【Orchestrator】意图: {intent}")
    return {"intent": intent}


def recognize_agent(state: MultiAgentState):
    result = "识别成功：晴天 - 周杰伦"
    return {"recognize_result": result, "song_name": "晴天"}


def info_agent(state: MultiAgentState):
    song = state.get("song_name") or "这首歌"
    # 尝试从 RAG 检索
    rag_text = "暂无"
    try:
        from src.utils.rag import hybrid_search
        results = hybrid_search(song, top_k=2)
        if results:
            rag_text = "\n".join([str(r["data"]) for r in results])
    except Exception:
        pass

    prompt = f"""你是音乐知识专家。用户在问关于《{song}》的信息。

【RAG 检索到的资料】
{rag_text}

【回答要求】
1. 如果检索到资料，基于资料回答。
2. 如果资料为空，但你能从歌名判断出歌手/风格（如"刘聪"、"Demo"、"丁世光"等关键词），结合你的音乐知识给出合理的介绍。
3. 不要直接说"我不了解"，要给用户提供有价值的内容。
4. 200 字以内，轻松友好的语气。
"""
    result = llm.invoke(prompt).content
    return {"info_result": result}


def recommend_agent(state: MultiAgentState):
    song = state.get("song_name") or "这首歌"
    prompt = f"""你是一位资深音乐DJ，用户刚听了《{song}》，想让你推荐3首相似风格的歌。

【硬性规则 - 必须遵守】
1. 你**必须**输出恰好3首推荐歌曲，格式为：「1. 歌名 - 歌手」
2. 每首歌后面跟一句话说明推荐理由
3. **绝对禁止**出现以下字眼："抱歉"、"我不了解"、"无法推荐"、"没有信息"
4. 即使你不熟悉这首歌，也要基于歌名/歌手的常见风格做合理推测
5. 如果歌名里能识别出歌手（比如丁世光、刘聪、周杰伦），就围绕这个歌手的风格推荐

【参考线索】
歌曲名: {song}

【示例输出格式】
1. 《XXX》- XX歌手：同样的都市R&B风格，氛围感强。
2. 《YYY》- YY歌手：慵懒的嗓音处理，情绪相似。
3. 《ZZZ》- ZZ歌手：编曲上都有低保真的复古感。

现在请直接输出3首推荐，不要有任何开场白。
"""
    result = llm.invoke(prompt).content
    return {"recommend_result": result}


def chat_agent(state: MultiAgentState):
    response = llm.invoke(state["user_input"]).content
    return {"final_answer": response}


def route_by_intent(state: MultiAgentState):
    intent = state.get("intent", "chat")
    return {
        "recognize": "recognize_agent",
        "info": "info_agent",
        "recommend": "recommend_agent",
        "chat": "chat_agent",
    }.get(intent, "chat_agent")


def synthesize(state: MultiAgentState):
    result = (state.get("recognize_result") or state.get("info_result") or
              state.get("recommend_result") or state.get("final_answer", "无结果"))
    return {"final_answer": result}


memory = MemorySaver()
graph = StateGraph(MultiAgentState)
graph.add_node("classify", classify_intent)
graph.add_node("recognize_agent", recognize_agent)
graph.add_node("info_agent", info_agent)
graph.add_node("recommend_agent", recommend_agent)
graph.add_node("chat_agent", chat_agent)
graph.add_node("synthesize", synthesize)

graph.add_edge(START, "classify")
graph.add_conditional_edges("classify", route_by_intent)
graph.add_edge("recognize_agent", "synthesize")
graph.add_edge("info_agent", "synthesize")
graph.add_edge("recommend_agent", "synthesize")
graph.add_edge("chat_agent", "synthesize")
graph.add_edge("synthesize", END)

app = graph.compile(checkpointer=memory)


if __name__ == '__main__':
    config = {"configurable": {"thread_id": "test_1"}}
    print(app.invoke({"user_input": "帮我识别这首歌"}, config)["final_answer"])
    print(app.invoke({"user_input": "那这首歌是谁唱的？"}, config)["final_answer"])
    print(app.invoke({"user_input": "推荐几首类似的"}, config)["final_answer"])