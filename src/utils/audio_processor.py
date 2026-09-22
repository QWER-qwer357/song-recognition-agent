import librosa
import numpy as np
import matplotlib.pyplot as plt

def load_audio(file_path, sr=22050, duration=30):
    """加载音频文件，返回波形和采样率"""
    y, sr = librosa.load(file_path, sr=sr, duration=duration)
    return y, sr

def get_spectrogram(y, sr):
    """计算频谱图（短时傅里叶变换）"""
    D = librosa.stft(y)
    S = librosa.amplitude_to_db(np.abs(D), ref=np.max)
    return S

def get_mel_spectrogram(y, sr, n_mels=128):
    """计算梅尔频谱图"""
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels)
    S_db = librosa.power_to_db(S, ref=np.max)
    return S_db

def plot_spectrogram(S, sr):
    """可视化"""
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(S, sr=sr, x_axis='time', y_axis='hz')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Spectrogram')
    plt.tight_layout()
    plt.savefig('spectrogram.png')
    plt.show()

if __name__ == '__main__':
    print("正在加载音频...")
    
    audio_path = 'songfile.mp3'  
    
    try:
        y, sr = librosa.load(audio_path, sr=22050)
        print(f"音频长度: {len(y)/sr:.1f}秒")
        print(f"采样率: {sr}")
        
        S = get_spectrogram(y, sr)
        print(f"频谱图形状: {S.shape}")
        
        mel_S = get_mel_spectrogram(y, sr)
        print(f"梅尔频谱图形状: {mel_S.shape}")
        
        print("正在绘图...")
        plot_spectrogram(S, sr)
        print("绘图完成 已保存为 spectrogram.png")

    except Exception as e:
        print(f"出错了 错误信息: {e}")