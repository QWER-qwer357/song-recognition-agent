import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

# 初始化大模型
llm = ChatOpenAI(
    model="glm-4-flash",
    temperature=0,
    api_key="xxx", 
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
    """节点1：意图分类"""
    prompt = f"""判断用户意图，只返回一个词：
    - recognize: 用户上传了音频或明确要求“识别这首歌”
    - info: 用户询问某首歌的信息、歌手、歌词。
    - recommend: 用户要求推荐歌曲
    - chat: 普通聊天

    用户输入：{state['user_input']}
    意图："""
    intent = llm.invoke(prompt).content.strip().lower()
    print(f"【Orchestrator】意图识别为: {intent}")
    return {"intent": intent}

def recognize_agent(state: MultiAgentState):
    """节点2a：识别 Agent"""
    result = "识别成功：晴天 - 周杰伦"
    return {"recognize_result": result, "song_name": "晴天"}

def info_agent(state: MultiAgentState):
    """节点2b：信息 Agent"""
    from src.utils.rag import hybrid_search
    query = state.get("song_name") or state["user_input"]
    results = hybrid_search(query, top_k=1)
    if results:
        data = results[0]["data"]
        result = f"歌曲《{data['song_name']}》- 歌手：{data['artist']}，歌词：{data['lyrics'][:20]}..."
    else:
        result = "未找到相关信息。"
    return {"info_result": result}

def recommend_agent(state: MultiAgentState):
    """节点2c：推荐 Agent"""
    result = "为您推荐：稻香、七里香、简单爱"
    return {"recommend_result": result}

def chat_agent(state: MultiAgentState):
    """节点2d：对话 Agent"""
    response = llm.invoke(state["user_input"]).content
    return {"final_answer": response}

def route_by_intent(state: MultiAgentState):
    """根据意图决定去哪个子 Agent"""
    intent = state.get("intent", "chat")
    routes = {
        "recognize": "recognize_agent",
        "info": "info_agent",
        "recommend": "recommend_agent",
        "chat": "chat_agent",
    }
    return routes.get(intent, "chat_agent")

def synthesize(state: MultiAgentState):
    """汇总各 Agent 结果"""
    result = (
        state.get("recognize_result") or 
        state.get("info_result") or 
        state.get("recommend_result") or 
        state.get("final_answer", "无结果")
    )
    return {"final_answer": result}

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

app = graph.compile()
if __name__ == '__main__':
    test_inputs = [
        "帮我识别一下这首歌是什么",
        "晴天是谁唱的？",
        "给我推荐几首歌",
        "今天天气真好啊"
    ]
    
    for text in test_inputs:
        print(f"\n--- 测试输入：{text} ---")
        result = app.invoke({"user_input": text})
        print(f"最终回答: {result['final_answer']}")