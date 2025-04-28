#!/usr/bin/env python3
import math
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, CheckButtons
import numpy as np
import sounddevice as sd

def test_sound():
    """测试音频输出"""
    sample_rate = 44100
    duration = 0.5
    frequency = 440  # A4音高

    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t) * 0.3
    
    print("Testing sound output (A4 - 440Hz)")
    sd.play(tone, sample_rate)
    sd.wait()

class FrequencyPlotter:
    def __init__(self):
        # 基本参数
        self.NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.show_all_notes = False
        self.current_scale = None
        self.current_root = 'C'
        
        # 添加音色选项
        self.TIMBRES = ['Piano', 'Guitar', 'Synth', 'Drum']
        self.current_timbre = 'Piano'
        
        # 音频参数
        self.sample_rate = 44100
        self.duration = 0.5
        
        # 创建图形
        self.fig = plt.figure(figsize=(15, 10))
        self.ax = self.fig.add_subplot(111)
        plt.subplots_adjust(left=0.1, bottom=0.25, right=0.95, top=0.95)
        
        # 生成数据
        self.n_values = list(range(-48, 40))
        self.frequencies = [440 * math.pow(2, n/12) for n in self.n_values]
        
        # 初始化
        self.setup_plot()
        self.setup_controls()
        self.setup_audio_events()
        self.update_plot()

    def setup_plot(self):
        """设置基本图形"""
        self.base_line, = self.ax.plot(self.n_values, self.frequencies, 'b-', 
                                     label='f = 440 × 2^(n/12)', linewidth=2)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_xlabel('Semitones from A4', fontsize=12)
        self.ax.set_ylabel('Frequency (Hz)', fontsize=12)

    def setup_controls(self):
        """设置控制按钮"""
        # Show All Notes checkbox
        check_ax = self.fig.add_axes([0.1, 0.12, 0.15, 0.05])
        self.check = CheckButtons(check_ax, ['Show All Notes'], [False])
        
        # Scale selector
        scale_ax = self.fig.add_axes([0.35, 0.05, 0.2, 0.1])
        self.scale_radio = RadioButtons(
            scale_ax,
            ['None', 'Major', 'Minor', 'Chromatic'],
            active=0
        )
        
        # Root note selector
        root_ax = self.fig.add_axes([0.65, 0.05, 0.25, 0.1])
        self.root_radio = RadioButtons(
            root_ax,
            self.NOTES,
            active=0
        )
        
        # 添加音色选择器
        timbre_ax = self.fig.add_axes([0.1, 0.05, 0.15, 0.05])
        self.timbre_radio = RadioButtons(
            timbre_ax,
            self.TIMBRES,
            active=0
        )
        
        # 设置字体大小
        [t.set_fontsize(10) for t in self.check.labels]
        [t.set_fontsize(10) for t in self.scale_radio.labels]
        [t.set_fontsize(10) for t in self.root_radio.labels]
        [t.set_fontsize(10) for t in self.timbre_radio.labels]
        
        # 添加标签
        self.fig.text(0.1, 0.17, 'Timbre:', fontsize=12)
        self.fig.text(0.35, 0.17, 'Scale Type:', fontsize=12)
        self.fig.text(0.65, 0.17, 'Root Note:', fontsize=12)
        
        # Connect events
        self.check.on_clicked(self.check_callback)
        self.scale_radio.on_clicked(self.scale_callback)
        self.root_radio.on_clicked(self.root_callback)
        self.timbre_radio.on_clicked(self.timbre_callback)

    def setup_audio_events(self):
        """设置音频事件"""
        self.fig.canvas.mpl_connect('button_press_event', self.on_plot_click)
        print("Audio events setup completed")

    def generate_piano_tone(self, frequency, t):
        """钢琴音色"""
        tone = np.sin(2 * np.pi * frequency * t) * 0.5
        tone += np.sin(4 * np.pi * frequency * t) * 0.25
        tone += np.sin(6 * np.pi * frequency * t) * 0.125
        return tone

    def generate_guitar_tone(self, frequency, t):
        """吉他音色"""
        tone = np.sin(2 * np.pi * frequency * t) * 0.5
        # 添加更多泛音
        for i in range(2, 6):
            tone += np.sin(2 * np.pi * frequency * i * t) * (0.25 / i)
        # 添加特征性的衰减
        decay = np.exp(-3 * t)
        return tone * decay

    def generate_synth_tone(self, frequency, t):
        """电子琴音色"""
        # 锯齿波
        sawtooth = 2 * (frequency * t - np.floor(0.5 + frequency * t))
        # 方波
        square = np.sign(np.sin(2 * np.pi * frequency * t))
        # 混合
        tone = sawtooth * 0.3 + square * 0.2
        return tone

    def generate_drum_tone(self, frequency, t):
        """鼓声音色"""
        # 使用噪声和快速衰减
        noise = np.random.rand(len(t)) * 2 - 1
        decay = np.exp(-30 * t)
        tone = noise * decay
        return tone

    def play_tone(self, frequency):
        """生成并播放音调，包含音色选择"""
        duration = self.duration
        sample_rate = self.sample_rate
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 根据选择的音色生成音调
        if self.current_timbre == 'Piano':
            tone = self.generate_piano_tone(frequency, t)
        elif self.current_timbre == 'Guitar':
            tone = self.generate_guitar_tone(frequency, t)
        elif self.current_timbre == 'Synth':
            tone = self.generate_synth_tone(frequency, t)
        elif self.current_timbre == 'Drum':
            tone = self.generate_drum_tone(frequency, t)
        
        # ADSR包络参数
        if self.current_timbre == 'Drum':
            attack, decay = 0.01, 0.1
            sustain_level, release = 0.3, 0.1
        else:
            attack, decay = 0.05, 0.1
            sustain_level, release = 0.7, 0.1
        
        # 创建ADSR包络
        attack_samples = int(attack * sample_rate)
        decay_samples = int(decay * sample_rate)
        release_samples = int(release * sample_rate)
        
        envelope = np.ones(len(t))
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[attack_samples:attack_samples+decay_samples] = \
            np.linspace(1, sustain_level, decay_samples)
        envelope[attack_samples+decay_samples:-release_samples] = sustain_level
        envelope[-release_samples:] = np.linspace(sustain_level, 0, release_samples)
        
        # 应用包络
        tone = tone * envelope * 0.3
        
        print(f"Playing {self.current_timbre} tone: {frequency:.1f} Hz")
        sd.play(tone, sample_rate)
        sd.wait()

    def get_scale_semitones(self, scale_type='major', root='C'):
        """获取音阶的半音序列"""
        if scale_type is None or scale_type.lower() == 'none':
            return []
            
        scales = {
            'major': [0, 2, 4, 5, 7, 9, 11],
            'minor': [0, 2, 3, 5, 7, 8, 10],
            'chromatic': list(range(12))
        }
        
        if scale_type.lower() not in scales:
            return []
            
        root_offset = self.NOTES.index(root.upper())
        scale_pattern = scales[scale_type.lower()]
        return [(x + root_offset) % 12 for x in scale_pattern]

    def get_note_name(self, semitones_from_a4):
        """根据与A4的半音距离获取音符名称"""
        note_index = (semitones_from_a4 + 9) % 12
        octave = 4 + (semitones_from_a4 + 9) // 12
        return f"{self.NOTES[note_index]}{octave}"

    def find_nearest_note(self, x, y):
        """找到最接近点击位置的音符"""
        x_tolerance = 1.0
        y_tolerance_percentage = 0.1
        
        notes_to_show = []
        if self.current_scale and self.current_scale.lower() != 'none':
            scale_semitones = self.get_scale_semitones(self.current_scale, self.current_root)
            notes_to_show = [n for n in self.n_values if (n + 9) % 12 in scale_semitones]
        elif self.show_all_notes:
            notes_to_show = self.n_values
        else:
            notes_to_show = list(range(-48, 40, 12))

        clicked_freq = 440 * math.pow(2, x/12)
        closest_note = None
        min_distance = float('inf')
        
        for note in notes_to_show:
            note_freq = 440 * math.pow(2, note/12)
            x_dist = abs(x - note)
            y_dist = abs(y - note_freq) / note_freq
            
            if x_dist <= x_tolerance and y_dist <= y_tolerance_percentage:
                distance = (x_dist * 0.3) + (y_dist * 0.7)
                if distance < min_distance:
                    min_distance = distance
                    closest_note = note

        if closest_note is not None:
            freq = 440 * math.pow(2, closest_note/12)
            return closest_note, freq
        return None

    def highlight_note(self, note, freq):
        """添加视觉反馈"""
        for artist in self.ax.lines:
            if hasattr(artist, 'highlight'):
                artist.remove()
        
        highlight = self.ax.plot(note, freq, 'yo', markersize=15, alpha=0.5, 
                               label='Playing')[0]
        highlight.highlight = True
        
        self.fig.canvas.draw_idle()
        plt.pause(0.2)
        highlight.remove()
        self.fig.canvas.draw_idle()

    def on_plot_click(self, event):
        """处理点击事件"""
        if event.inaxes != self.ax:
            return

        nearest = self.find_nearest_note(event.xdata, event.ydata)
        if nearest:
            note, freq = nearest
            note_name = self.get_note_name(note)
            print(f"Playing {self.current_timbre}: {note_name} ({freq:.1f} Hz)")
            
            self.highlight_note(note, freq)
            self.play_tone(freq)

    def update_plot(self):
        """更新图形显示"""
        for artist in self.ax.lines[1:]:
            artist.remove()
        for artist in self.ax.texts[:]:
            artist.remove()

        notes_to_show = []
        if self.current_scale and self.current_scale.lower() != 'none':
            scale_semitones = self.get_scale_semitones(self.current_scale, self.current_root)
            notes_to_show = [n for n in self.n_values if (n + 9) % 12 in scale_semitones]
        elif self.show_all_notes:
            notes_to_show = self.n_values
        else:
            notes_to_show = list(range(-48, 40, 12))

        if notes_to_show:
            frequencies_to_show = [440 * math.pow(2, n/12) for n in notes_to_show]
            self.ax.plot(notes_to_show, frequencies_to_show, 'ro')

            for n, f in zip(notes_to_show, frequencies_to_show):
                self.ax.annotate(
                    f'{self.get_note_name(n)}\n{f:.1f}Hz',
                    (n, f),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=8,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.7)
                )

        self.ax.plot(0, 440, 'go', markersize=10, label='A4 (440 Hz)')

        self.ax.text(0.02, 0.98, 
                    'Piano Range:\nA0: 27.5 Hz\nA4: 440 Hz\nC8: 4186 Hz',
                    transform=self.ax.transAxes,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        title = '12-Tone Equal Temperament (Piano 88 Keys)\nClick on notes to play'
        if self.current_scale and self.current_scale.lower() != 'none':
            title += f'\n{self.current_root} {self.current_scale} scale'
        self.ax.set_title(title, fontsize=14)

        self.fig.canvas.draw_idle()

    def check_callback(self, label):
        self.show_all_notes = not self.show_all_notes
        self.update_plot()

    def scale_callback(self, label):
        self.current_scale = label
        self.update_plot()

    def root_callback(self, label):
        self.current_root = label
        if not self.current_scale or self.current_scale.lower() == 'none':
            self.current_scale = 'Major'
        self.update_plot()

    def timbre_callback(self, label):
        """处理音色选择"""
        self.current_timbre = label
        print(f"Changed timbre to: {label}")

    def show(self):
        plt.show()

if __name__ == "__main__":
    print("Testing sound output...")
    test_sound()
    
    print("Initializing frequency plotter...")
    plotter = FrequencyPlotter()
    plotter.show()
