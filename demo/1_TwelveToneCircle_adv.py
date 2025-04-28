#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Wedge
from matplotlib.widgets import Button, RadioButtons
import sounddevice as sd
import matplotlib
import platform

# 根据操作系统设置中文字体
if platform.system() == 'Darwin':  # macOS
    matplotlib.rc("font", family='Arial Unicode MS')
elif platform.system() == 'Windows':  # Windows
    matplotlib.rc("font", family='Microsoft YaHei')
else:  # Linux
    matplotlib.rc("font", family='WenQuanYi Micro Hei')

plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

print("Libraries loaded successfully")

class TwelveToneCircle:
    def __init__(self):
        print("Initializing TwelveToneCircle")
        self.fig = plt.figure(figsize=(11.2, 11.2))
        self.ax = self.fig.add_subplot(111)
        plt.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.25)
        
        # 添加罗马数字映射
        self.roman_numerals = {
            0: 'I',
            1: 'II♭',
            2: 'II',
            3: 'III♭',
            4: 'III',
            5: 'IV',
            6: 'V♭',
            7: 'V',
            8: 'VI♭',
            9: 'VI',
            10: 'VII♭',
            11: 'VII'
        }
        
        # 音程中英文对照
        self.intervals = {
            0: "Root (根音)",
            1: "Minor 2nd (小二度)",
            2: "Major 2nd (大二度)",
            3: "Minor 3rd (小三度)",
            4: "Major 3rd (大三度)",
            5: "Perfect 4th (纯四度)",
            6: "Tritone (三全音)",
            7: "Perfect 5th (纯五度)",
            8: "Minor 6th (小六度)",
            9: "Major 6th (大六度)",
            10: "Minor 7th (小七度)",
            11: "Major 7th (大七度)"
        }
        
        self.degree_texts = {}
        
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.set_xlim(-1.3, 1.3)
        self.ax.set_ylim(-1.3, 1.3)
        
        self.notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.selected_notes = []
        self.note_objects = {}
        self.note_texts = {}
        
        # 和弦类型定义（带中文注释）
        self.chord_types = {
            'Major Triad (大三和弦)': [0, 4, 7],
            'Minor Triad (小三和弦)': [0, 3, 7],
            'Dim Triad (减三和弦)': [0, 3, 6],
            'Aug Triad (增三和弦)': [0, 4, 8],
            'Major 7th (大七和弦)': [0, 4, 7, 11],
            'Minor 7th (小七和弦)': [0, 3, 7, 10],
            'Dom 7th (属七和弦)': [0, 4, 7, 10]
        }
        
        self.current_root = 'C'
        self.current_chord_type = None
        
        self.draw_circle()
        self.setup_controls()
        
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        print("Initialization complete")

    def draw_circle(self):
        print("Drawing circle")
        radius = 0.9
        circle = Circle((0, 0), radius, fill=False, linewidth=2)
        self.ax.add_artist(circle)
        
        for i, note in enumerate(self.notes):
            angle = 90 - i * 30
            x = radius * np.cos(np.radians(angle))
            y = radius * np.sin(np.radians(angle))
            
            wedge = Wedge((0, 0), radius+0.15, angle-12, angle+12, 
                         width=0.35, fc='lightgray', ec='black', alpha=0.6)
            self.ax.add_patch(wedge)
            self.note_objects[note] = wedge
            
            text = self.ax.text(x*1.15, y*1.15, note, ha='center', va='center',
                              fontsize=18, fontweight='bold')
            self.note_texts[note] = text
            
            print(f"Added note {note} at angle {angle}")
        
        self.update_degree_labels()

    def setup_controls(self):
        print("Setting up controls")
        
        # Root Note selector
        root_label_y = 0.20
        root_buttons_y = 0.15
        plt.figtext(0.1, root_label_y, 'Root Note:', fontsize=14, fontweight='bold')
        
        button_width = 0.06
        button_spacing = 0.005
        self.root_buttons = []
        
        for i, note in enumerate(self.notes):
            x = 0.1 + i * (button_width + button_spacing)
            button_ax = plt.axes([x, root_buttons_y, button_width, 0.04])
            button = Button(button_ax, note)
            button.label.set_fontsize(12)
            button.on_clicked(lambda event, n=note: self.on_root_select(n))
            self.root_buttons.append(button)
            if note == self.current_root:
                button.color = 'yellow'
                button.ax.set_facecolor('yellow')
        
        # Chord Type selector（调整宽度以适应更长的文本）
        chord_label_y = 0.13
        chord_buttons_y = 0.08
        plt.figtext(0.1, chord_label_y, 'Chord Type:', fontsize=14, fontweight='bold')
        
        chord_button_width = 0.12  # 增加按钮宽度
        chord_button_spacing = 0.005
        self.chord_buttons = []
        
        for i, chord_type in enumerate(self.chord_types.keys()):
            x = 0.1 + i * (chord_button_width + chord_button_spacing)
            button_ax = plt.axes([x, chord_buttons_y, chord_button_width, 0.04])
            button = Button(button_ax, chord_type)
            button.label.set_fontsize(9)  # 略微减小字体以适应更长的文本
            button.on_clicked(lambda event, ct=chord_type: self.on_chord_select(ct))
            self.chord_buttons.append(button)
        
        # Play and Clear buttons
        button_y = 0.02
        play_ax = plt.axes([0.35, button_y, 0.15, 0.04])
        self.play_button = Button(play_ax, 'Play', color='lightgreen')
        self.play_button.label.set_fontsize(14)
        self.play_button.on_clicked(self.play_chord)
        
        clear_ax = plt.axes([0.55, button_y, 0.15, 0.04])
        self.clear_button = Button(clear_ax, 'Clear', color='lightcoral')
        self.clear_button.label.set_fontsize(14)
        self.clear_button.on_clicked(self.clear_selection)
    def play_single_note(self, frequency):
        """播放单个音符"""
        try:
            sample_rate = 44100
            duration = 0.3  # 单音持续时间较短
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            
            # 生成音色
            tone = 0.2 * np.sin(2 * np.pi * frequency * t)
            tone += 0.1 * np.sin(4 * np.pi * frequency * t)
            tone += 0.05 * np.sin(6 * np.pi * frequency * t)
            
            # 应用ADSR包络
            attack = int(0.05 * sample_rate)
            release = int(0.1 * sample_rate)
            envelope = np.ones_like(t)
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[-release:] = np.linspace(1, 0, release)
            
            tone = tone * envelope * 0.5
            
            sd.play(tone, sample_rate)
            sd.wait()
        except Exception as e:
            print(f"Error playing sound: {str(e)}")

    def update_degree_labels(self):
        # 清除现有的级数标签
        for text in self.degree_texts.values():
            text.remove()
        self.degree_texts.clear()
        
        # 计算外圈半径
        radius = 1.2
        
        # 为每个音符添加级数标签
        root_index = self.notes.index(self.current_root)
        for i, note in enumerate(self.notes):
            interval = (i - root_index) % 12
            degree = self.roman_numerals[interval]
            
            angle = 90 - i * 30
            x = radius * np.cos(np.radians(angle))
            y = radius * np.sin(np.radians(angle))
            
            text = self.ax.text(x, y, degree, ha='center', va='center',
                               fontsize=14, color='darkblue',
                               bbox=dict(facecolor='white', alpha=0.7))
            self.degree_texts[note] = text
        
        self.fig.canvas.draw()

    def on_root_select(self, note):
        print(f"Root note changed to {note}")
        for button in self.root_buttons:
            if button.label.get_text() == note:
                button.color = 'yellow'
                button.ax.set_facecolor('yellow')
            else:
                button.color = 'white'
                button.ax.set_facecolor('white')
        
        self.current_root = note
        self.update_degree_labels()
        
        if self.current_chord_type:
            self.update_chord()
        self.fig.canvas.draw_idle()

    def on_chord_select(self, chord_type):
        print(f"Chord type changed to {chord_type}")
        for button in self.chord_buttons:
            if button.label.get_text() == chord_type:
                button.color = 'yellow'
                button.ax.set_facecolor('yellow')
            else:
                button.color = 'white'
                button.ax.set_facecolor('white')
        
        self.current_chord_type = chord_type
        self.update_chord()
        self.fig.canvas.draw_idle()

    def update_chord(self):
        print(f"Updating chord: {self.current_root} {self.current_chord_type}")
        for note in self.selected_notes:
            self.highlight_note(note, False)
        self.selected_notes = []
        
        if not self.current_chord_type:
            return

        intervals = self.chord_types[self.current_chord_type]
        
        root_index = self.notes.index(self.current_root)
        chord_notes = []
        for interval in intervals:
            note_index = (root_index + interval) % 12
            chord_notes.append(self.notes[note_index])
        
        self.selected_notes = chord_notes
        for note in chord_notes:
            self.highlight_note(note, True)
        
        self.update_interval_labels()
        print(f"Updated chord: {chord_notes}")
        self.fig.canvas.draw()

    def play_chord(self, event):
        if not self.selected_notes:
            return
        
        try:
            sample_rate = 44100
            duration = 1.0
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            
            chord = np.zeros_like(t)
            for note in self.selected_notes:
                note_index = self.notes.index(note)
                base_freq = 440 * 2**((note_index - self.notes.index('A')) / 12)
                
                chord += 0.2 * np.sin(2 * np.pi * base_freq * t)
                chord += 0.1 * np.sin(4 * np.pi * base_freq * t)
                chord += 0.05 * np.sin(6 * np.pi * base_freq * t)
            
            attack = int(0.1 * sample_rate)
            release = int(0.2 * sample_rate)
            envelope = np.ones_like(t)
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[-release:] = np.linspace(1, 0, release)
            
            chord = chord * envelope
            chord = chord / np.max(np.abs(chord)) * 0.5
            
            sd.play(chord, sample_rate)
            sd.wait()
            
        except Exception as e:
            print(f"Error playing sound: {str(e)}")

    def highlight_note(self, note, selected=True):
        wedge = self.note_objects[note]
        text = self.note_texts[note]
        
        if selected:
            wedge.set_fc('yellow')
            wedge.set_alpha(0.9)
            text.set_color('red')
            text.set_fontsize(22)
            wedge.set_edgecolor('red')
            wedge.set_linewidth(2)
        else:
            wedge.set_fc('lightgray')
            wedge.set_alpha(0.6)
            text.set_color('black')
            text.set_fontsize(18)
            wedge.set_edgecolor('black')
            wedge.set_linewidth(1)
            
        self.fig.canvas.draw()

    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        
        r = np.sqrt(event.xdata**2 + event.ydata**2)
        angle = np.degrees(np.arctan2(event.ydata, event.xdata))
        angle = (90 - angle) % 360
        
        click_tolerance = 15
        radius_min = 0.55
        radius_max = 1.25
        
        if radius_min <= r <= radius_max:
            note_angle = int((angle + click_tolerance/2) / 30) % 12
            note = self.notes[note_angle]
            
            # 播放点击的音符声音
            note_index = self.notes.index(note)
            freq = 440 * 2**((note_index - self.notes.index('A')) / 12)
            self.play_single_note(freq)
            
            if note in self.selected_notes:
                self.selected_notes.remove(note)
                self.highlight_note(note, False)
            else:
                self.selected_notes.append(note)
                self.highlight_note(note, True)
            self.update_interval_labels()

    def update_interval_labels(self):
        for txt in self.ax.texts:
            if txt.get_text() not in self.notes and txt.get_text() not in self.roman_numerals.values():
                txt.remove()
        
        if len(self.selected_notes) > 1:
            root = self.current_root if self.current_root in self.selected_notes else self.selected_notes[0]
            root_index = self.notes.index(root)
            
            for note in self.selected_notes:
                if note != root:
                    interval = (self.notes.index(note) - root_index) % 12
                    interval_name = self.intervals[interval]
                    
                    angle1 = 90 - self.notes.index(root) * 30
                    angle2 = 90 - self.notes.index(note) * 30
                    mid_angle = (angle1 + angle2) / 2
                    
                    x = 0.5 * np.cos(np.radians(mid_angle))
                    y = 0.5 * np.sin(np.radians(mid_angle))
                    
                    self.ax.text(x, y, interval_name, ha='center', va='center',
                               fontsize=12, color='blue',
                               bbox=dict(facecolor='white', alpha=0.7))
        
        self.fig.canvas.draw()

    def clear_selection(self, event):
        for note in self.selected_notes:
            self.highlight_note(note, False)
        self.selected_notes = []
        self.update_interval_labels()
        
        if self.current_chord_type:
            for button in self.chord_buttons:
                if button.label.get_text() == self.current_chord_type:
                    button.color = 'white'
                    button.ax.set_facecolor('white')
        self.current_chord_type = None
        
        self.update_degree_labels()
        self.fig.canvas.draw()

    def show(self):
        plt.show()

if __name__ == "__main__":
    print("Starting program")
    try:
        print("Testing sound system...")
        test_duration = 0.1
        test_sample_rate = 44100
        test_tone = np.sin(2 * np.pi * 440 * np.linspace(0, test_duration, 
                          int(test_sample_rate * test_duration)))
        sd.play(test_tone, test_sample_rate)
        sd.wait()
        print("Sound test successful")
        
        circle = TwelveToneCircle()
        circle.show()
    except Exception as e:
        print(f"Error: {str(e)}")

