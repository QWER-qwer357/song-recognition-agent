"""
自动测试脚本：从曲库里随机截 10 个片段，上传后端识别，自动对答案。
输出：曲库总数、准确率、平均响应时间。
"""
import os
import sys
import time
import random
import requests
from pydub import AudioSegment

# ============ 配置 ============
MP3_DIR = "data/library/mp3"
CLIPS_DIR = "data/test_clips"
API_URL = "http://127.0.0.1:8010"
NUM_TESTS = 10          # 测试多少首歌
CLIP_DURATION = 10      # 每个片段截多少秒
START_OFFSET = 5       # 从第30秒开始截（模拟从歌曲中间听）

os.makedirs(CLIPS_DIR, exist_ok=True)


def make_test_clips():
    """从 mp3 曲库里随机截取测试片段"""
    all_songs = [f for f in os.listdir(MP3_DIR) if f.lower().endswith(".mp3")]
    if len(all_songs) < NUM_TESTS:
        print(f"⚠️ 曲库只有 {len(all_songs)} 首，少于 {NUM_TESTS} 首，将全部使用。")
    chosen = random.sample(all_songs, min(NUM_TESTS, len(all_songs)))

    clips = []
    for fname in chosen:
        song_name = os.path.splitext(fname)[0]
        src = os.path.join(MP3_DIR, fname)
        try:
            audio = AudioSegment.from_file(src)
            # 如果音频不够长，从头截
            if len(audio) < (START_OFFSET + CLIP_DURATION) * 1000:
                start = 0
            else:
                start = random.randint(START_OFFSET, len(audio) // 1000 - CLIP_DURATION - 1) * 1000
            clip = audio[start:start + CLIP_DURATION * 1000]
            clip_path = os.path.join(CLIPS_DIR, f"{song_name}_clip.mp3")
            clip.export(clip_path, format="mp3")
            clips.append({"path": clip_path, "expected": song_name})
            print(f"  ✂️ 生成片段: {song_name}_clip.mp3")
        except Exception as e:
            print(f"  ❌ 截取失败 {fname}: {e}")
    return clips


def recognize(clip_path):
    """上传片段并轮询结果，返回 (识别的歌名, 耗时秒) 或 (None, 耗时)"""
    start_time = time.time()
    try:
        with open(clip_path, "rb") as f:
            r = requests.post(f"{API_URL}/recognize", files={"file": f}, timeout=30)
        data = r.json()

        # 异步：拿到 session_id 后轮询
        if "session_id" in data:
            sid = data["session_id"]
            for _ in range(40):
                time.sleep(1.5)
                res = requests.get(f"{API_URL}/result/{sid}", timeout=10)
                res_data = res.json()
                if res_data.get("status") == "completed":
                    result = res_data.get("result") or {}
                    return result.get("song_name"), time.time() - start_time
                if res_data.get("status") == "error":
                    return None, time.time() - start_time
            return None, time.time() - start_time

        # 同步：直接返回结果
        if "result" in data:
            result = data["result"] or {}
            return result.get("song_name"), time.time() - start_time
        return None, time.time() - start_time
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return None, time.time() - start_time


def main():
    print("=" * 60)
    print("🎵 听歌识曲系统 · 自动准确率测试")
    print("=" * 60)

    # 曲库统计
    total_songs = len([f for f in os.listdir(MP3_DIR) if f.lower().endswith(".mp3")])
    print(f"\n📚 曲库总数: {total_songs} 首\n")

    # 生成测试片段
    print(f"✂️ 正在生成 {NUM_TESTS} 个测试片段...")
    clips = make_test_clips()
    print(f"\n✅ 生成 {len(clips)} 个测试片段\n")

    # 逐个测试
    print("🎧 开始识别测试...\n")
    correct = 0
    total_time = 0
    results = []

    for i, clip in enumerate(clips, 1):
        print(f"[{i}/{len(clips)}] 测试: {clip['expected']}")
        recognized, elapsed = recognize(clip["path"])
        total_time += elapsed

        if recognized and (clip["expected"] in recognized or recognized in clip["expected"]):
            correct += 1
            results.append((clip["expected"], recognized, elapsed, "✅"))
            print(f"  ✅ 识别正确: {recognized}  ({elapsed:.2f}s)")
        else:
            results.append((clip["expected"], recognized or "未识别", elapsed, "❌"))
            print(f"  ❌ 识别错误: 期望「{clip['expected']}」, 得到「{recognized or '未识别'}」  ({elapsed:.2f}s)")
        print()

    # 汇总
    accuracy = correct / len(clips) * 100 if clips else 0
    avg_time = total_time / len(clips) if clips else 0

    print("=" * 60)
    print("📊 测试报告")
    print("=" * 60)
    print(f"曲库总数:      {total_songs} 首")
    print(f"测试样本:      {len(clips)} 个")
    print(f"识别正确:      {correct} 个")
    print(f"识别准确率:    {accuracy:.1f}%")
    print(f"平均响应时间:  {avg_time:.2f} 秒")
    print("=" * 60)

    print("\n💡 把下面这句话填进简历/README：")
    print(f"曲库 {total_songs} 首，识别准确率 {accuracy:.0f}%，平均响应 {avg_time:.1f}s。")
    print()


if __name__ == "__main__":
    main()