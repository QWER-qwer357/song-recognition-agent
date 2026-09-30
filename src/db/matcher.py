from src.db.database import SessionLocal, Song, Fingerprint
from collections import defaultdict


def store_fingerprints(db, song_name, hashes, file_path=None, artist=None):
    """存储歌曲指纹到数据库"""
    song = Song(name=song_name, file_path=file_path, artist=artist)
    db.add(song)
    db.flush()
    fingerprints = [
        Fingerprint(song_id=song.id, hash_value=str(h), offset=offset)
        for h, offset in hashes
    ]
    db.add_all(fingerprints)
    db.commit()
    return song.id


def match_song(db, hashes, threshold=10):
    """
    真正的 Shazam 式匹配：用「时间偏移一致性」过滤误匹配。
    
    原理：
    1. 对每个命中哈希，计算「数据库偏移 - 查询偏移」
    2. 正确匹配的歌曲，所有命中哈希的时间偏移应该一致（形成峰值）
    3. 误匹配的时间偏移会随机散布，形不成峰值
    4. 取「同一 (song_id, offset) 组合的最大命中数」作为得分
    """
    if not hashes:
        return {"status": "no_match", "message": "未提取到任何指纹"}

    # query 哈希 -> 偏移 映射
    query_offsets = {str(h): offset for h, offset in hashes}
    hash_list = list(query_offsets.keys())

    # 批量查询命中
    matches = db.query(Fingerprint).filter(
        Fingerprint.hash_value.in_(hash_list)
    ).all()

    if not matches:
        return {"status": "no_match", "message": "未找到匹配的歌曲，请尝试重新录制"}

    # 统计 (song_id, 时间偏移差) 的出现次数
    offset_counter = defaultdict(int)
    for fp in matches:
        query_offset = query_offsets.get(fp.hash_value)
        if query_offset is None:
            continue
        offset_diff = fp.offset - query_offset
        offset_counter[(fp.song_id, offset_diff)] += 1

    if not offset_counter:
        return {"status": "no_match", "message": "未找到匹配的歌曲"}

    # 取「同一个时间偏移下，命中数最多」的歌曲
    (best_song_id, best_offset), best_score = max(
        offset_counter.items(), key=lambda x: x[1]
    )

    if best_score < threshold:
        return {
            "status": "low_confidence",
            "best_score": best_score,
            "message": f"匹配度过低（{best_score}），建议重新录制更清晰的音频"
        }

    song = db.query(Song).filter(Song.id == best_song_id).first()
    return {
        "status": "matched",
        "song_name": song.name,
        "artist": song.artist,
        "match_score": best_score,
        "offset": best_offset,
        "total_hashes": len(hashes)
    }