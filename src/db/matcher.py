from src.db.database import SessionLocal, Song, Fingerprint
from collections import defaultdict

def store_fingerprints(db, song_name, hashes, file_path=None):
    """存储歌曲指纹到database"""
    song = Song(name=song_name, file_path=file_path)
    db.add(song)
    db.flush() 
    
    # 插入指纹
    fingerprints = [
        Fingerprint(song_id=song.id, hash_value=str(h), offset=offset)
        for h, offset in hashes
    ]
    db.add_all(fingerprints)
    db.commit()
    return song.id

def match_song(db, hashes, threshold=10):
    """使用指纹哈希匹配歌曲 返回最佳匹配"""
    hash_list = [str(h) for h, _ in hashes]

    # 查询
    matches = db.query(Fingerprint).filter(
        Fingerprint.hash_value.in_(hash_list)
    ).all()

    #分组 统计匹配数量
    song_scores = defaultdict(int)
    for fp in matches:
        song_scores[fp.song_id] += 1
        
    if not song_scores:
        return None
        
    # 匹配
    best_song_id = max(song_scores, key=song_scores.get)
    best_score = song_scores[best_song_id]
    
    if best_score < threshold:
        return None
        
    song = db.query(Song).filter(Song.id == best_song_id).first()
    return {
        "song_name": song.name,
        "artist": song.artist,
        "match_score": best_score,
        "total_hashes": len(hashes)
    }