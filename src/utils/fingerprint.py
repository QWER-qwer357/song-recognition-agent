import librosa
import numpy as np
from scipy.ndimage import maximum_filter

def compute_spectrogram(y, sr, n_fft=2048, hop_length=512):
    """计算STFT频谱图"""
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    return S

def find_peaks(S, amp_min=10):
    """找局部峰值点"""
    struct = maximum_filter(S, size=(20, 20))
    peaks = (S == struct) & (S >= amp_min)
    freq_idx, time_idx = np.where(peaks)
    return freq_idx, time_idx

def generate_hashes(freq_idx, time_idx, fan_value=5):
    """峰值配对生成指纹哈希"""
    hashes = []
    for i in range(len(freq_idx)):
        for j in range(1, fan_value + 1):
            if i + j < len(freq_idx):
                freq1 = freq_idx[i]
                freq2 = freq_idx[i + j]
                t1 = time_idx[i]
                t2 = time_idx[i + j]
                hash_val = hash((int(freq1), int(freq2), int(t2 - t1)))
                hashes.append((hash_val, int(t1)))
    return hashes

def fingerprint_file(file_path):
    y, sr = librosa.load(file_path, sr=22050, duration=30)
    S = compute_spectrogram(y, sr)
    freq_idx, time_idx = find_peaks(S)
    hashes = generate_hashes(freq_idx, time_idx)
    return hashes

if __name__ == '__main__':
    print("正在加载音频...")
    my_audio_path = 'songfile.mp3'  
    try:
        print("开始提取指纹...")
        hashes = fingerprint_file(my_audio_path)
        print(f"成功生成 {len(hashes)} 个指纹哈希 ")
        print("前10个指纹 (哈希值, 时间偏移):")
        for h in hashes[:10]:
            print(h)
    except Exception as e:
        print(f"出错了 错误信息: {e}")