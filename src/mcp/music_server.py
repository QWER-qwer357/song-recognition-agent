from mcp.server.fastmcp import FastMCP

mcp = FastMCP("music-tools")
@mcp.tool()
def search_music(query: str) -> str:
    """输入歌曲名或歌手名 返回搜索结果。"""
    return f"搜索『{query}』的结果：周杰伦 - 晴天、稻香、七里香"

@mcp.tool()
def get_lyrics(song: str, artist: str) -> str:
    """获取歌曲歌词 输入歌曲名和歌手名。"""
    lyrics = "故事的小黄花 从出生那年就飘着 童年的荡秋千 随记忆一直晃到现在..."
    return f"《{song}》- {artist} 的歌词：{lyrics}"

if __name__ == "__main__":
    print("MCP Server 启动中... 等待客户端连接。")
    mcp.run()