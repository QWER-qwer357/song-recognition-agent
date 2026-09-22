import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import numpy as np
print("正在加载本地向量模型...")
model = SentenceTransformer("all-MiniLM-L6-v2")

es = Elasticsearch("http://localhost:9200")

def create_index():
    """创建索引 同时支持 BM25 全文检索和向量检索"""
    if es.indices.exists(index="songs"):
        es.indices.delete(index="songs")
        
    es.indices.create(index="songs", body={
        "mappings": {
            "properties": {
                "song_name": {"type": "text"},
                "artist": {"type": "text"},
                "lyrics": {"type": "text"},
                "lyrics_vector": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    })

def index_song(song_name, artist, lyrics):
    """索引一首歌：同时存原文和向量"""
    vec = model.encode(lyrics).tolist()
    es.index(index="songs", body={
        "song_name": song_name, 
        "artist": artist, 
        "lyrics": lyrics, 
        "lyrics_vector": vec
    })
    es.indices.refresh(index="songs")
    print(f"已存入歌曲：{song_name} - {artist}")

def hybrid_search(query, top_k=5):
    """混合检索：BM25 + 向量 用 RRF 融合"""
    query_vec = model.encode(query).tolist()
    
    bm25_results = es.search(index="songs", body={
        "size": top_k, 
        "query": {"match": {"lyrics": query}}
    })
    
    vector_results = es.search(index="songs", body={
        "knn": {
            "field": "lyrics_vector", 
            "query_vector": query_vec, 
            "k": top_k, 
            "num_candidates": 100
        }
    })
    
    rrf_scores = {}
    for i, hit in enumerate(bm25_results["hits"]["hits"]):
        doc_id = hit["_id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (60 + i + 1)
    for i, hit in enumerate(vector_results["hits"]["hits"]):
        doc_id = hit["_id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (60 + i + 1)
        
    sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    results = []
    for doc_id, score in sorted_ids:
        doc = es.get(index="songs", id=doc_id)
        results.append({"data": doc["_source"], "score": score})
    return results

if __name__ == '__main__':
    print("=== 测试 RAG 系统 ===")
    create_index()
    
    index_song("晴天", "周杰伦", "故事的小黄花 从出生那年就飘着 童年的荡秋千 随记忆一直晃到现在")
    index_song("稻香", "周杰伦", "对这个世界如果你有太多的抱怨 跌倒了就不敢继续往前走")
    
    print("\n=== 搜索：童年记忆 ===")
    results = hybrid_search("童年记忆 荡秋千", top_k=2)
    for r in results:
        print(f"歌曲：{r['data']['song_name']}，歌手：{r['data']['artist']}，分数：{r['score']:.4f}")