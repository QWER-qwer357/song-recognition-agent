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

def match_song(db, hashes, threshold=50):
    """用指纹哈希匹配歌曲，返回最佳匹配。
    阈值默认调高到 50 避免短音频/噪音导致的误匹配。
    """
    hash_list = [str(h) for h, _ in hashes]
    matches = db.query(Fingerprint).filter(
        Fingerprint.hash_value.in_(hash_list)
    ).all()

    song_scores = defaultdict(int)
    for fp in matches:
        song_scores[fp.song_id] += 1

    if not song_scores:
        return {"status": "no_match", "message": "未找到匹配的歌曲，请尝试重新录制"}

    best_song_id = max(song_scores, key=song_scores.get)
    best_score = song_scores[best_song_id]

    if best_score < threshold:
        return {
            "status": "low_confidence",
            "best_score": best_score,
            "message": f"匹配度过低（{best_score}），建议重新录制一段更清晰的音频"
        }

    song = db.query(Song).filter(Song.id == best_song_id).first()
    return {
        "status": "matched",
        "song_name": song.name,
        "artist": song.artist,
        "match_score": best_score,
        "total_hashes": len(hashes)
    }