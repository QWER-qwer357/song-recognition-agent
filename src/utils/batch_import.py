import os
import sys
import shutil
from pydub import AudioSegment

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.fingerprint import fingerprint_file
from src.db.database import get_db
from src.db.matcher import store_fingerprints

# 路径配置
RAW_DIR = "data/library/raw"
MP3_DIR = "data/library/mp3"

def convert_to_mp3():
    """把 raw 文件夹里的各种格式音频 统一转码成 mp3 存入 mp3 文件夹"""
    os.makedirs(MP3_DIR, exist_ok=True)
    print(f"开始扫描 {RAW_DIR} 下的音频文件...")
    
    count = 0
    for filename in os.listdir(RAW_DIR):
        file_path = os.path.join(RAW_DIR, filename)
        if not os.path.isfile(file_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.mp3', '.wav', '.flac', '.m4a']:
            print(f"跳过非音频文件: {filename}")
            continue
            
        name = os.path.splitext(filename)[0]
        target_mp3 = os.path.join(MP3_DIR, f"{name}.mp3")
        
        if os.path.exists(target_mp3):
            print(f"[已存在] {name}.mp3 跳过")
            count += 1
            continue

        if ext == '.mp3':
            shutil.copy(file_path, target_mp3)
            print(f"[复制] {filename} -> mp3 文件夹")
            count += 1
            continue
            
        try:
            print(f"[转码中] {filename} -> {name}.mp3")
            audio = AudioSegment.from_file(file_path)
            audio.export(target_mp3, format="mp3")
            count += 1
        except Exception as e:
            print(f"转码失败 {filename}: {e}")
    print(f"转码完成 共处理 {count} 个文件。\n")

def batch_fingerprint():
    """遍历文件夹 自动提取指纹并存入数据库"""
    print(f"开始批量提取指纹并入库...")
    db = next(get_db())
    success = 0
    
    for filename in os.listdir(MP3_DIR):
        if not filename.lower().endswith('.mp3'):
            continue
            
        file_path = os.path.join(MP3_DIR, filename)
        song_name = os.path.splitext(filename)[0]
        
        try:
            print(f"正在处理: {song_name} ...")
            hashes = fingerprint_file(file_path)
            song_id = store_fingerprints(db, song_name, hashes, file_path)
            print(f"入库成功 (ID: {song_id}, 指纹数: {len(hashes)})")
            success += 1
        except Exception as e:
            print(f"入库失败 {song_name}: {e}")
            
    db.close()
    print(f"\n共成功入库 {success} 首歌曲")

if __name__ == '__main__':
    print("=== 本地音乐库自动建库工具 ===")
    convert_to_mp3()
    batch_fingerprint()