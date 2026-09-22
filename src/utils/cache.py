import redis
import json
import hashlib
import time
from contextlib import contextmanager

# 连接本地 Docker 里的 Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def cache_song_result(audio_hash, result, ttl=3600):
    """缓存识别结果 1小时过期"""
    key = f"song:result:{audio_hash}"
    r.setex(key, ttl, json.dumps(result))

def get_cached_result(audio_hash):
    """获取识别结果"""
    key = f"song:result:{audio_hash}"
    val = r.get(key)
    return json.loads(val) if val else None

@contextmanager
def redis_lock(lock_key, timeout=10):
    """简单的 Redis 分布式锁"""
    lock_id = str(time.time())
    try:
        acquired = r.set(lock_key, lock_id, nx=True, px=timeout * 1000)
        if not acquired:
            raise Exception(f"获取锁失败: {lock_key}")
        yield
    finally:
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        r.eval(lua_script, 1, lock_key, lock_id)

def increment_song_play(song_name):
    """歌曲被识别一次 排行榜+1"""
    r.zincrby("song:rankings", 1, song_name)

def get_top_songs(n=10):
    """获取识别次数最多的 N 首歌"""
    return r.zrevrange("song:rankings", 0, n - 1, withscores=True)

def save_session(session_id, messages, ttl=1800):
    """保存对话会话 30 分钟过期"""
    r.setex(f"session:{session_id}", ttl, json.dumps(messages))

def get_session(session_id):
    """获取会话"""
    val = r.get(f"session:{session_id}")
    return json.loads(val) if val else None
def save_session(session_id, data, ttl=1800):
    """保存会话/任务状态 30 分钟过期"""
    r.setex(f"session:{session_id}", ttl, json.dumps(data))

def get_session(session_id):
    """获取会话/任务状态"""
    val = r.get(f"session:{session_id}")
    return json.loads(val) if val else None