#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.widgets import Button, RadioButtons
import sounddevice as sd

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # macOS系统可用
plt.rcParams['axes.unicode_minus'] = False

class PianoTeacher:
    def __init__(self):
        print("Initializing Piano Teacher")
        self.fig = plt.figure(figsize=(16, 10))
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.25)
        
        # 创建钢琴显示区域和控制区域
        self.piano_ax = self.fig.add_subplot(211)  # 上半部分是钢琴
        self.piano_ax.set_title("Piano (88 keys)")
        
        # 定义音符和频率
        self.base_notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.octaves = range(0, 8)  # 0-8八度
        
        # 生成所有键的信息
        self.keys = []  # 存储所有键的信息
        self.key_rectangles = {}  # 存储键的图形对象
        self.selected_keys = []  # 当前选中的键
        self.pressed_keys = []   # 当前按下的键
        
        # 定义和弦（添加中文注释）
        self.triads = {
            'Major (大三和弦)': [0, 4, 7],
            'Minor (小三和弦)': [0, 3, 7],
            'Diminished (减三和弦)': [0, 3, 6],
            'Augmented (增三和弦)': [0, 4, 8]
        }
        
        self.seventh_chords = {
            'Major 7th (大七和弦)': [0, 4, 7, 11],
            'Minor 7th (小七和弦)': [0, 3, 7, 10],
            'Dominant 7th (属七和弦)': [0, 4, 7, 10],
            'Half Dim (半减七和弦)': [0, 3, 6, 10]
        }
        
        self.extended_chords = {
            '9th (九和弦)': [0, 4, 7, 10, 14],
            '11th (十一和弦)': [0, 4, 7, 10, 14, 17],
            '13th (十三和弦)': [0, 4, 7, 10, 14, 17, 21]
        }
        
        self.current_root = 'A4'  # A4 = 440Hz
        self.current_chord_type = None
        
        self.setup_piano()
        self.setup_controls()
        
        # 添加鼠标事件
        self.fig.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        
        print("Initialization complete")

    def setup_piano(self):
        """设置钢琴键盘显示"""
        self.piano_ax.clear()
        self.piano_ax.set_xlim(0, 88)
        self.piano_ax.set_ylim(0, 2)
        
        # 绘制白键和黑键
        white_key_width = 1.0
        black_key_width = 0.6
        
        white_index = 0
        for i in range(88):
            note_index = i % 12
            octave = (i + 9) // 12  # 从A0开始
            note = self.base_notes[note_index]
            
            # 确定是否为黑键
            is_black = '#' in note
            
            if not is_black:
                # 绘制白键
                rect = Rectangle((white_index, 0), white_key_width, 2,
                               fc='white', ec='black')
                self.piano_ax.add_patch(rect)
                
                # 存储键的信息
                key_info = {
                    'note': f"{note}{octave}",
                    'rect': rect,
                    'index': i,
                    'freq': 440 * 2**((i - 48)/12),  # A4 = 440Hz
                    'is_black': False,
                    'x': white_index,
                    'width': white_key_width
                }
                self.keys.append(key_info)
                self.key_rectangles[f"{note}{octave}"] = rect
                
                # 在关键位置添加标注
                if note == 'C':
                    self.piano_ax.text(white_index + 0.5, -0.2, f'C{octave}', 
                                     ha='center', va='top')
                
                white_index += white_key_width
            else:
                # 绘制黑键
                prev_white_x = white_index - white_key_width
                rect = Rectangle((prev_white_x + white_key_width - black_key_width/2, 1),
                               black_key_width, 1,
                               fc='black', ec='black')
                self.piano_ax.add_patch(rect)
                
                # 存储键的信息
                key_info = {
                    'note': f"{note}{octave}",
                    'rect': rect,
                    'index': i,
                    'freq': 440 * 2**((i - 48)/12),  # A4 = 440Hz
                    'is_black': True,
                    'x': prev_white_x + white_key_width - black_key_width/2,
                    'width': black_key_width
                }
                self.keys.append(key_info)
                self.key_rectangles[f"{note}{octave}"] = rect
        
        # 标注 A4 = 440Hz
        a4_x = self.keys[48]['x']  # A4的位置
        self.piano_ax.text(a4_x + 0.5, -0.2, 'A4 (440Hz)', ha='center', 
                          va='top', color='red', fontweight='bold')
        
        self.piano_ax.axis('off')
    def setup_controls(self):
        """设置控制按钮"""
        # 第一行：音符选择
        plt.figtext(0.1, 0.2, '选择根音:', fontsize=12, fontweight='bold')
        base_notes_ax = plt.axes([0.1, 0.15, 0.3, 0.05])
        self.base_notes_radio = RadioButtons(base_notes_ax, 
                                           ['C', 'D', 'E', 'F', 'G', 'A', 'B'])
        
        plt.figtext(0.45, 0.2, '选择八度:', fontsize=12, fontweight='bold')
        octaves_ax = plt.axes([0.45, 0.15, 0.4, 0.05])
        self.octaves_radio = RadioButtons(octaves_ax, 
                                        [str(i) for i in range(9)])
        
        # 第二行：三和四和弦
        plt.figtext(0.1, 0.13, '三和弦:', fontsize=12, fontweight='bold')
        triads_ax = plt.axes([0.1, 0.08, 0.35, 0.05])
        self.triads_radio = RadioButtons(triads_ax, list(self.triads.keys()))
        
        plt.figtext(0.5, 0.13, '七和弦:', fontsize=12, fontweight='bold')
        seventh_ax = plt.axes([0.5, 0.08, 0.35, 0.05])
        self.seventh_radio = RadioButtons(seventh_ax, list(self.seventh_chords.keys()))
        
        # 第三行：扩展和弦
        plt.figtext(0.1, 0.06, '扩展和弦:', fontsize=12, fontweight='bold')
        extended_ax = plt.axes([0.1, 0.01, 0.35, 0.05])
        self.extended_radio = RadioButtons(extended_ax, list(self.extended_chords.keys()))
        
        # 调整所有RadioButtons的字体大小
        for radio in [self.base_notes_radio, self.octaves_radio, 
                     self.triads_radio, self.seventh_radio, self.extended_radio]:
            for label in radio.labels:
                label.set_fontsize(10)
        
        # 绑定事件处理
        self.base_notes_radio.on_clicked(self.on_note_select)
        self.octaves_radio.on_clicked(self.on_octave_select)
        self.triads_radio.on_clicked(self.on_chord_select)
        self.seventh_radio.on_clicked(self.on_chord_select)
        self.extended_radio.on_clicked(self.on_chord_select)

    def get_frequency(self, note):
        """计算给定音符的频率"""
        for key in self.keys:
            if key['note'] == note:
                return key['freq']
        return None

    def generate_note_sound(self, freq, duration=0.5):
        """生成钢琴音色"""
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 基频和泛音（模拟钢琴音色）
        tone = np.sin(2 * np.pi * freq * t) * 0.4
        tone += np.sin(4 * np.pi * freq * t) * 0.2
        tone += np.sin(6 * np.pi * freq * t) * 0.1
        tone += np.sin(8 * np.pi * freq * t) * 0.05
        
        # ADSR包络
        attack = int(0.02 * sample_rate)
        decay = int(0.1 * sample_rate)
        sustain_level = 0.7
        release = int(0.2 * sample_rate)
        
        envelope = np.ones_like(t)
        envelope[:attack] = np.linspace(0, 1, attack)
        envelope[attack:attack+decay] = np.linspace(1, sustain_level, decay)
        envelope[-release:] = np.linspace(sustain_level, 0, release)
        
        return tone * envelope

    def play_chord(self, notes):
        """播放和弦"""
        if not notes:
            return
            
        try:
            duration = 0.5
            sample_rate = 44100
            chord = np.zeros(int(sample_rate * duration))
            
            for note in notes:
                freq = self.get_frequency(note)
                if freq:
                    chord += self.generate_note_sound(freq, duration)
            
            # 归一化并控制音量
            chord = chord / np.max(np.abs(chord)) * 0.5
            
            sd.play(chord, sample_rate)
            
        except Exception as e:
            print(f"Error playing sound: {str(e)}")

    def highlight_keys(self, notes, highlight=True):
        """高亮显示按键"""
        for note in notes:
            if note in self.key_rectangles:
                rect = self.key_rectangles[note]
                if highlight:
                    rect.set_facecolor('yellow' if '#' not in note else 'gray')
                else:
                    rect.set_facecolor('white' if '#' not in note else 'black')
        
        self.fig.canvas.draw()
    def on_mouse_press(self, event):
        """处理鼠标按下事件"""
        if event.inaxes != self.piano_ax:
            return
            
        # 查找被点击的键
        for key in self.keys:
            if (key['x'] <= event.xdata < key['x'] + key['width'] and
                (not key['is_black'] or (key['is_black'] and event.ydata > 1))):
                
                self.pressed_keys.append(key['note'])
                self.highlight_keys([key['note']], True)
                self.play_chord([key['note']])
                
                # 显示正在播放的音符和频率
                print(f"Playing: {key['note']} ({key['freq']:.1f} Hz)")
                break

    def on_mouse_release(self, event):
        """处理鼠标释放事件"""
        if self.pressed_keys:
            self.highlight_keys(self.pressed_keys, False)
            self.pressed_keys = []

    def on_note_select(self, label):
        """处理音符选择"""
        self.update_current_root()

    def on_octave_select(self, label):
        """处理八度选择"""
        self.update_current_root()

    def on_chord_select(self, label):
        """处理和弦选择"""
        # 清除其他和弦选择器的选择
        if label in self.triads:
            self.current_chord_type = ('triad', label)
            self.seventh_radio.set_active(-1)
            self.extended_radio.set_active(-1)
        elif label in self.seventh_chords:
            self.current_chord_type = ('seventh', label)
            self.triads_radio.set_active(-1)
            self.extended_radio.set_active(-1)
        else:
            self.current_chord_type = ('extended', label)
            self.triads_radio.set_active(-1)
            self.seventh_radio.set_active(-1)
        
        self.update_chord()

    def update_current_root(self):
        """更新当前根音"""
        note = self.base_notes_radio.value_selected
        octave = self.octaves_radio.value_selected
        if note and octave:
            self.current_root = f"{note}{octave}"
            self.update_chord()

    def update_chord(self):
        """更新和弦显示"""
        if not self.current_chord_type or not self.current_root:
            return
            
        # 清除之前的高亮
        self.highlight_keys(self.selected_keys, False)
        self.selected_keys = []
        
        # 获取和弦音程
        chord_type, chord_name = self.current_chord_type
        if chord_type == 'triad':
            intervals = self.triads[chord_name]
        elif chord_type == 'seventh':
            intervals = self.seventh_chords[chord_name]
        else:
            intervals = self.extended_chords[chord_name]
        
        # 计算和弦音符
        root_index = next((i for i, k in enumerate(self.keys) 
                          if k['note'] == self.current_root), None)
        
        if root_index is not None:
            for interval in intervals:
                note_index = root_index + interval
                if 0 <= note_index < len(self.keys):
                    self.selected_keys.append(self.keys[note_index]['note'])
            
            # 高亮显示和弦音符
            self.highlight_keys(self.selected_keys, True)
            
            # 播放和弦
            self.play_chord(self.selected_keys)
            
            # 显示和弦信息
            print(f"Playing chord: {self.current_root} {chord_name}")
            print(f"Notes: {', '.join(self.selected_keys)}")

    def show(self):
        plt.show()

if __name__ == "__main__":
    print("Starting Piano Teacher")
    piano = PianoTeacher()
    piano.show()
