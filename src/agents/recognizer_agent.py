import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent

llm = ChatOpenAI(
    model="glm-4-flash",
    temperature=0,
    api_key="xxx",
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

@tool
def recognize_song(audio_file_path: str) -> str:
    """识别音频文件是什么歌。参数为本地音频文件路径。"""
    try:
        from src.utils.fingerprint import fingerprint_file
        from src.db.database import get_db
        from src.db.matcher import match_song
        
        hashes = fingerprint_file(audio_file_path)
        db = next(get_db())
        result = match_song(db, hashes)
        if result:
            return f"识别成功！歌曲：{result['song_name']}，匹配度：{result['match_score']}。"
        return "未能识别该歌曲，请尝试录制更清晰的片段。"
    except Exception as e:
        return f"识别过程出错：{str(e)}"

@tool
def get_song_info(song_name: str) -> str:
    """查询歌曲详细信息。"""
    song_db = {
        "第一首歌": {"artist": "NastelBom", "year": "2025"}
    }
    info = song_db.get(song_name)
    if info:
        return f"歌曲《{song_name}》- 歌手：{info['artist']}，发行年份：{info['year']}"
    return f"未找到歌曲《{song_name}》的信息。"
tools = [recognize_song, get_song_info]

agent = create_react_agent(
    llm, 
    tools,
    prompt="你是一个听歌识曲助手。可以调用工具来识别歌曲或查询信息。"
)

if __name__ == '__main__':
    print("=== 测试 1：查歌曲信息 ===")
    result = agent.invoke({"messages": [("user", "帮我查一下《第一首歌》是谁唱的")]})
    print("Agent 回答:", result["messages"][-1].content)
    print()
    
    print("=== 测试 2：识别歌曲 ===")
    result = agent.invoke({"messages": [("user", "帮我识别一下 songfile.mp3 这是什么歌")]})
    print("Agent 回答:", result["messages"][-1].content)