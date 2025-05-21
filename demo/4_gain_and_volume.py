#!/usr/bin/env python3

import numpy as np
import soundfile as sf
from scipy import signal
import matplotlib.pyplot as plt

def apply_gain(audio_data, gain_db):
    """
    应用增益调整
    gain_db: 增益值(dB)
    返回: 经过增益调整的音频数据
    """
    # 将dB转换为线性增益
    linear_gain = 10 ** (gain_db / 20.0)
    return audio_data * linear_gain

def apply_volume(audio_data, volume_factor):
    """
    应用音量调整
    volume_factor: 音量调整因子 (0.0 到 1.0)
    返回: 经过音量调整的音频数据
    """
    return audio_data * volume_factor

# 示例使用
def main():
    # 1. 生成测试音频信号
    sample_rate = 44100  # 采样率
    duration = 3  # 持续时间(秒)
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 生成1000Hz的正弦波
    frequency = 1000
    audio_signal = np.sin(2 * np.pi * frequency * t)

    # 2. 应用不同的增益值
    gain_db_positive = 6  # +6dB增益
    gain_db_negative = -6  # -6dB增益
    
    audio_gain_up = apply_gain(audio_signal, gain_db_positive)
    audio_gain_down = apply_gain(audio_signal, gain_db_negative)

    # 3. 应用不同的音量值
    volume_up = 0.8    # 80%音量
    volume_down = 0.2  # 20%音量
    
    audio_vol_up = apply_volume(audio_signal, volume_up)
    audio_vol_down = apply_volume(audio_signal, volume_down)

    # 4. 绘制波形对比图
    plt.figure(figsize=(15, 10))
    
    # 原始信号
    plt.subplot(5, 1, 1)
    plt.plot(t[:1000], audio_signal[:1000])
    plt.title('Original Signal')
    
    # 增益+6dB
    plt.subplot(5, 1, 2)
    plt.plot(t[:1000], audio_gain_up[:1000])
    plt.title('Gain +6dB')
    
    # 增益-6dB
    plt.subplot(5, 1, 3)
    plt.plot(t[:1000], audio_gain_down[:1000])
    plt.title('Gain -6dB')
    
    # 音量80%
    plt.subplot(5, 1, 4)
    plt.plot(t[:1000], audio_vol_up[:1000])
    plt.title('Volume 80%')
    
    # 音量20%
    plt.subplot(5, 1, 5)
    plt.plot(t[:1000], audio_vol_down[:1000])
    plt.title('Volume 20%')
    
    plt.tight_layout()
    plt.show()

    # 5. 保存音频文件
    sf.write('original.wav', audio_signal, sample_rate)
    sf.write('gain_up.wav', audio_gain_up, sample_rate)
    sf.write('gain_down.wav', audio_gain_down, sample_rate)
    sf.write('volume_up.wav', audio_vol_up, sample_rate)
    sf.write('volume_down.wav', audio_vol_down, sample_rate)

if __name__ == "__main__":
    main()
