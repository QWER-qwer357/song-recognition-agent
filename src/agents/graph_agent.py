import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

from src.agents.memory import AgentMemory
memory = AgentMemory(max_short_term=10)

llm = ChatOpenAI(
    model="glm-4-flash",
    temperature=0,
    api_key="xxx",
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

@tool
def recognize_song(audio_file_path: str) -> str:
    """识别音频文件是什么歌 参数为本地音频文件路径"""
    from src.utils.fingerprint import fingerprint_file
    from src.db.database import get_db
    from src.db.matcher import match_song
    try:
        hashes = fingerprint_file(audio_file_path)
        db = next(get_db())
        result = match_song(db, hashes)
        if result:
            return f"识别成功 歌曲：{result['song_name']}，匹配度：{result['match_score']}。"
        return "未能识别该歌曲。"
    except Exception as e:
        return f"识别过程出错：{str(e)}"

@tool
def get_song_info(song_name: str) -> str:
    """查询歌曲详细信息。输入歌名，返回歌手、年份。"""
    song_db = {"第一首歌": {"artist": "NastelBom",  "year": "2025"}}
    info = song_db.get(song_name)
    if info:
        return f"歌曲《{song_name}》- 歌手：{info['artist']}..."
    return f"未找到歌曲《{song_name}》的信息。"

tools = [recognize_song, get_song_info]
llm_with_tools = llm.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

def call_llm(state: AgentState):
    """节点1：调用大模型"""
    last_user_msg = state["messages"][-1].content
    
    context = memory.get_context(last_user_msg)
    
    system_prompt = f"你是一个听歌识曲助手。这是关于用户的历史信息：{context['long_term_retrieved']}。用户画像：{context['user_profile']}。请结合这些信息回答。"
    
    messages_with_memory = [SystemMessage(content=system_prompt)] + state["messages"]
    
    response = llm_with_tools.invoke(messages_with_memory)
    return {"messages": [response]}

def call_tool(state: AgentState):
    last_msg = state["messages"][-1]
    results = []
    if last_msg.tool_calls:
        for tc in last_msg.tool_calls:
            if tc["name"] == "recognize_song":
                result = recognize_song.invoke(tc["args"])
            elif tc["name"] == "get_song_info":
                result = get_song_info.invoke(tc["args"])
            else:
                result = "未知工具"
            results.append(ToolMessage(content=result, tool_call_id=tc["id"]))
    return {"messages": results}

def should_continue(state: AgentState):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return END

graph = StateGraph(AgentState)
graph.add_node("llm", call_llm)
graph.add_node("tools", call_tool)
graph.add_edge(START, "llm")
graph.add_conditional_edges("llm", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "llm")
app = graph.compile()

if __name__ == '__main__':
    print("=== 测试记忆接入 ===")
    result = app.invoke({"messages": [HumanMessage(content="我喜欢周杰伦的歌")]})
    print("Agent 回答:", result["messages"][-1].content)
    
    result = app.invoke({"messages": [HumanMessage(content="帮我查一下《第一首歌》是谁唱的")]})
    print("Agent 回答:", result["messages"][-1].content)