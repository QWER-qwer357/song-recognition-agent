import os
import sys
import shutil
import re
from pydub import AudioSegment

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.fingerprint import fingerprint_file
from src.db.database import get_db
from src.db.matcher import store_fingerprints

RAW_DIR = "data/library/raw"
MP3_DIR = "data/library/mp3"

def parse_song_info(filename):
    """从文件名解析 歌名 和 歌手。
    规则：优先按 " - " 拆分，从左边提取中文作为歌手名。
    例如：
        "KEY_L刘聪 - Hey KONG (Demo)" -> ("Hey KONG (Demo)", "刘聪")
        "周杰伦 - 晴天" -> ("晴天", "周杰伦")
        "稻香.mp3" -> ("稻香", None)
    """
    name = os.path.splitext(filename)[0]
    if ' - ' in name:
        left, right = name.split(' - ', 1)
        chinese = re.findall(r'[\u4e00-\u9fa5]+', left)
        if chinese:
            artist = ''.join(chinese)
            return right.strip(), artist
        return right.strip(), left.strip()
    return name, None


def convert_to_mp3():
    os.makedirs(MP3_DIR, exist_ok=True)
    print(f"开始扫描 {RAW_DIR}...")
    count = 0
    for filename in os.listdir(RAW_DIR):
        file_path = os.path.join(RAW_DIR, filename)
        if not os.path.isfile(file_path): continue
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.mp3', '.wav', '.flac', '.m4a']:
            print(f"跳过非音频文件: {filename}")
            continue
        target_mp3 = os.path.join(MP3_DIR, os.path.splitext(filename)[0] + ".mp3")
        if os.path.exists(target_mp3):
            print(f"  [已存在] {os.path.basename(target_mp3)}")
            count += 1
            continue
        if ext == '.mp3':
            shutil.copy(file_path, target_mp3)
            count += 1
            continue
        try:
            print(f"[转码中] {filename}")
            audio = AudioSegment.from_file(file_path)
            audio.export(target_mp3, format="mp3")
            count += 1
        except Exception as e:
            print(f"转码失败 {filename}: {e}")
    print(f"转码完成，共 {count} 个文件。\n")


def batch_fingerprint():
    print(f"开始批量提取指纹并入库...")
    db = next(get_db())
    success = 0
    for filename in os.listdir(MP3_DIR):
        if not filename.lower().endswith('.mp3'): continue
        file_path = os.path.join(MP3_DIR, filename)
        song_name, artist = parse_song_info(filename)
        try:
            print(f"正在处理: {song_name} — {artist or '未知歌手'}")
            hashes = fingerprint_file(file_path)
            song_id = store_fingerprints(db, song_name, hashes, file_path, artist=artist)
            print(f"入库成功 (ID: {song_id}, 指纹数: {len(hashes)}, 歌手: {artist})")
            success += 1
        except Exception as e:
            print(f"入库失败 {song_name}: {e}")
    db.close()
    print(f"\n全部完成！共成功入库 {success} 首。")


if __name__ == '__main__':
    print("=== 本地音乐库自动建库工具 ===")
    convert_to_mp3()
    batch_fingerprint()