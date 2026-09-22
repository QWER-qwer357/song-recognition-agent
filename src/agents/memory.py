import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
import chromadb
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer

class AgentMemory:
    """Agent记忆系统：短期记忆 + 长期记忆"""
    
    def __init__(self, max_short_term=10):
        self.short_term = []
        self.max_short_term = max_short_term
        
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.chroma = chromadb.PersistentClient(path="./data/chroma")
        self.collection = self.chroma.get_or_create_collection("long_term_memory")
        
        self.user_profile = {
            "favorite_artists": [],
            "favorite_genres": [],
            "recent_songs": [],
        }
        
        self.llm = ChatOpenAI(
            model="glm-4-flash",
            temperature=0,
            api_key="xxx",  
            base_url="https://open.bigmodel.cn/api/paas/v4/"
        )

    def add_to_short_term(self, role, content):
        """添加到短期记忆 超过上限时进行摘要压缩"""
        self.short_term.append({"role": role, "content": content})
        if len(self.short_term) > self.max_short_term:
            self._summarize_and_compress()

    def _summarize_and_compress(self):
        """把旧对话压缩成摘要 存入长期记忆"""
        old_messages = self.short_term[:self.max_short_term // 2]
        summary = self.llm.invoke(f"请把以下对话摘要成关键信息：\n{old_messages}").content
        
        # 存入长期记忆
        self._add_to_long_term(f"对话摘要：{summary}")
        
        self.short_term = [{"role": "system", "content": f"之前的对话摘要：{summary}"}] + self.short_term[self.max_short_term // 2:]

    def _add_to_long_term(self, text, metadata=None):
        """存入长期记忆"""
        vec = self.embed_model.encode(text).tolist()
        
        if not metadata:
            metadata = {"source": "agent_memory"}
            
        self.collection.add(
            documents=[text],
            embeddings=[vec],
            ids=[f"mem_{self.collection.count()}"],
            metadatas=[metadata]
        )
    def retrieve_long_term(self, query, top_k=3):
        """从长期记忆中检索信息"""
        vec = self.embed_model.encode(query).tolist()
        results = self.collection.query(query_embeddings=[vec], n_results=top_k)
        return results["documents"][0] if results["documents"] else []

    def update_profile(self, key, value):
        """更新用户画像"""
        if key in self.user_profile:
            if value not in self.user_profile[key]:
                self.user_profile[key].append(value)

    def get_context(self, query):
        """获取完整上下文：短期记忆 + 长期记忆检索 + 用户画像"""
        long_term = self.retrieve_long_term(query)
        return {
            "short_term": self.short_term,
            "long_term_retrieved": long_term,
            "user_profile": self.user_profile
        }

if __name__ == '__main__':
    print("正在初始化记忆系统...")
    memory = AgentMemory(max_short_term=4)
    
    print("=== 测试短期记忆（滑动窗口） ===")
    memory.add_to_short_term("user", "我喜欢周杰伦的歌")
    memory.add_to_short_term("assistant", "好的，记下了")
    memory.add_to_short_term("user", "最近有什么新歌吗")
    memory.add_to_short_term("assistant", "有的")
    #第5轮
    memory.add_to_short_term("user", "帮我识别一下 songfile.mp3")
    
    print(f"当前短期记忆: {memory.short_term}")
    
    print("\n=== 测试长期记忆检索 ===")
    long_term_result = memory.retrieve_long_term("我喜欢听谁歌")
    print(f"长期记忆检索结果: {long_term_result}")
    
    print("\n=== 测试用户画像 ===")
    memory.update_profile("favorite_artists", "周杰伦")
    print(f"用户画像: {memory.user_profile}")