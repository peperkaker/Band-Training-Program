#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, RadioButtons, Slider
import sounddevice as sd
from matplotlib.patches import Rectangle, Circle, Arrow
import threading
import time
from matplotlib.gridspec import GridSpec

class RhythmTeacher:
    def __init__(self):
        print("Initializing Rhythm Teacher")
        self.fig = plt.figure(figsize=(15, 10))
        self.gs = GridSpec(2, 2, figure=self.fig)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # macOS系统
        plt.rcParams['axes.unicode_minus'] = False

        # 创建四个区域
        self.theory_ax = self.fig.add_subplot(self.gs[0, 0])  # 理论区
        self.visual_ax = self.fig.add_subplot(self.gs[0, 1])  # 可视化区
        self.practice_ax = self.fig.add_subplot(self.gs[1, 0])  # 练习区
        self.score_ax = self.fig.add_subplot(self.gs[1, 1])    # 评分区
        
        # 课程内容
        self.lessons = {
            "基础节拍": {
                "theory": [
                    "节拍是音乐的心跳",
                    "基本拍子：2/4, 3/4, 4/4",
                    "强拍和弱拍的概念"
                ],
                "exercises": [
                    {"name": "单拍练习", "pattern": [1]},
                    {"name": "强弱拍练习", "pattern": [1, 0]},
                    {"name": "四拍子练习", "pattern": [1, 0, 0.5, 0]}
                ]
            },
            "常见节奏型": {
                "theory": [
                    "行进曲：| ♩ ♩ | ♩ ♩ |",
                    "圆舞曲：| ♩ ♪ ♪ | ♩ ♪ ♪ |",
                    "伦巴：  | ♩ ♪♪ ♩ | ♩ ♪♪ ♩ |"
                ],
                "exercises": [
                    {"name": "行进曲练习", "pattern": [1, 1, 1, 1]},
                    {"name": "圆舞曲练习", "pattern": [1, 0.5, 0.5]},
                    {"name": "伦巴练习", "pattern": [1, 0.5, 0.5, 1]}
                ]
            },
            "复合拍子": {
                "theory": [
                    "6/8拍：两个主要重拍",
                    "切分音：重音位置改变",
                    "混合拍子：如5/4, 7/8"
                ],
                "exercises": [
                    {"name": "6/8练习", "pattern": [1, 0, 0, 0.5, 0, 0]},
                    {"name": "切分音练习", "pattern": [0.5, 1, 0.5]},
                    {"name": "5/4练习", "pattern": [1, 0, 1, 0, 0]}
                ]
            }
        }
        
        self.current_lesson = "基础节拍"
        self.current_exercise = 0
        self.is_playing = False
        self.play_thread = None
        self.tempo = 90  # 默认速度
        self.score = 0
        self.user_hits = []
        
        self.setup_gui()
        self.update_display()
        
        # 添加键盘事件监听
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        print("Initialization complete")

    def setup_gui(self):
        # 理论区域设置
        self.theory_ax.set_title("理论讲解", pad=20)
        self.theory_ax.axis('off')
        
        # 可视化区域设置
        self.visual_ax.set_title("节拍可视化", pad=20)
        self.visual_ax.set_aspect('equal')
        self.visual_ax.set_xlim(-1.2, 1.2)
        self.visual_ax.set_ylim(-1.2, 1.2)
        
        # 练习区域控件
        lesson_ax = plt.axes([0.1, 0.35, 0.3, 0.1])
        self.lesson_radio = RadioButtons(lesson_ax, list(self.lessons.keys()))
        self.lesson_radio.on_clicked(self.change_lesson)
        
        # 速度控制
        tempo_ax = plt.axes([0.1, 0.25, 0.3, 0.02])
        self.tempo_slider = Slider(tempo_ax, 'BPM', 40, 200, valinit=self.tempo)
        self.tempo_slider.on_changed(self.change_tempo)
        
        # 播放按钮
        play_ax = plt.axes([0.1, 0.15, 0.15, 0.05])
        self.play_button = Button(play_ax, 'Play', color='lightgreen')
        self.play_button.on_clicked(self.toggle_play)

    def update_display(self):
        # 更新理论显示
        self.theory_ax.clear()
        self.theory_ax.set_title("理论讲解", pad=20)
        self.theory_ax.axis('off')
        
        theory_text = self.lessons[self.current_lesson]["theory"]
        for i, text in enumerate(theory_text):
            self.theory_ax.text(0.1, 0.8-i*0.2, text, fontsize=12)
        
        # 更新可视化显示
        self.visual_ax.clear()
        self.visual_ax.set_title("节拍可视化", pad=20)
        self.visual_ax.set_aspect('equal')
        self.visual_ax.set_xlim(-1.2, 1.2)
        self.visual_ax.set_ylim(-1.2, 1.2)
        
        current_pattern = self.lessons[self.current_lesson]["exercises"][self.current_exercise]["pattern"]
        self.draw_rhythm_circle(current_pattern)
        
        # 更新评分显示
        self.update_score()
        
        self.fig.canvas.draw()

    def draw_rhythm_circle(self, pattern):
        n_beats = len(pattern)
        radius = 0.8
        
        for i, strength in enumerate(pattern):
            angle = 90 - (i * 360 / n_beats)  # 从顶部开始，顺时针
            x = radius * np.cos(np.radians(angle))
            y = radius * np.sin(np.radians(angle))
            
            # 绘制节拍点
            color = 'yellow' if strength == 1 else 'lightblue' if strength == 0.5 else 'lightgray'
            circle = Circle((x, y), 0.1, fc=color, ec='black')
            self.visual_ax.add_artist(circle)
            
            # 添加数字标签
            self.visual_ax.text(x*1.2, y*1.2, str(i+1), 
                              ha='center', va='center', fontsize=14)

    def on_key_press(self, event):
        """处理键盘输入（空格键打拍子）"""
        if event.key == ' ' and self.is_playing:
            self.user_hits.append(time.time())
            self.evaluate_timing()

    def evaluate_timing(self):
        """评估用户打拍准确性"""
        if not self.user_hits:
            return
        
        pattern = self.lessons[self.current_lesson]["exercises"][self.current_exercise]["pattern"]
        beat_interval = 60.0 / self.tempo
        
        # 计算期望的打拍时间
        expected_times = []
        base_time = self.user_hits[0]
        for i, strength in enumerate(pattern):
            if strength > 0:  # 只检查需要打拍的位置
                expected_times.append(base_time + i * beat_interval)
        
        # 计算实际打拍与期望时间的差异
        timing_errors = []
        for hit in self.user_hits:
            nearest_expected = min(expected_times, key=lambda x: abs(x - hit))
            error = abs(hit - nearest_expected)
            timing_errors.append(error)
        
        # 更新分数
        avg_error = np.mean(timing_errors)
        self.score = max(0, 100 - avg_error * 100)
        self.update_score()

    def update_score(self):
        """更新分数显示"""
        self.score_ax.clear()
        self.score_ax.set_title("练习评分", pad=20)
        self.score_ax.axis('off')
        
        self.score_ax.text(0.5, 0.5, f'得分: {self.score:.1f}', 
                          ha='center', va='center', fontsize=20)

    def play_rhythm(self):
        """播放节拍器"""
        pattern = self.lessons[self.current_lesson]["exercises"][self.current_exercise]["pattern"]
        
        while self.is_playing:
            for strength in pattern:
                if not self.is_playing:
                    break
                    
                if strength > 0:  # 只在需要声音的位置播放
                    self.play_click(strength)
                
                time.sleep(60.0 / self.tempo)

    def play_click(self, strength):
        """生成并播放节拍声音"""
        sample_rate = 44100
        duration = 0.05
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        freq = 800 if strength < 1 else 440
        click = np.sin(2 * np.pi * freq * t)
        
        envelope = np.exp(-10 * t)
        click = click * envelope * strength * 0.5
        
        sd.play(click, sample_rate)

    def toggle_play(self, event):
        """切换播放状态"""
        if self.is_playing:
            self.is_playing = False
            self.play_button.label.set_text('Play')
            self.play_button.color = 'lightgreen'
        else:
            self.is_playing = True
            self.play_button.label.set_text('Stop')
            self.play_button.color = 'lightcoral'
            
            self.user_hits = []  # 重置用户打拍记录
            self.play_thread = threading.Thread(target=self.play_rhythm)
            self.play_thread.start()
        
        self.fig.canvas.draw()

    def change_lesson(self, label):
        """切换课程"""
        self.current_lesson = label
        self.current_exercise = 0
        self.update_display()

    def change_tempo(self, val):
        """改变速度"""
        self.tempo = val

    def show(self):
        plt.show()

if __name__ == "__main__":
    print("Starting Rhythm Teacher")
    teacher = RhythmTeacher()
    teacher.show()
