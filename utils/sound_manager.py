import pygame
import os
import threading
import sys
from typing import Optional

class SoundManager:
    def __init__(self):
        # 初始化pygame mixer
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            # 设置音量为最大
            pygame.mixer.music.set_volume(1.0)
        except Exception as e:
            print(f"pygame mixer初始化失败: {e}")
        
        self.sound_thread = None
        self.stop_flag = False
        self.current_action = None
        
    def _get_sound_path(self, filename: str) -> Optional[str]:
        """获取音效文件路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的路径
            base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境路径 - 从utils目录回到项目根目录
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        sound_path = os.path.join(base_path, "sounds", filename)
        return sound_path if os.path.exists(sound_path) else None
        
    def _play_sound_loop(self, initial_sound: str, loop_sound: str):
        """音效播放线程"""
        try:
            # 检查mixer是否初始化
            if not pygame.mixer.get_init():
                print("pygame mixer未初始化，尝试重新初始化...")
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.music.set_volume(1.0)
            
            # 播放初始音效
            initial_path = self._get_sound_path(initial_sound)
            if initial_path:
                print(f"播放初始音效: {initial_path}")
                pygame.mixer.music.load(initial_path)
                pygame.mixer.music.play()
                
                # 等待初始音效播放完成
                while pygame.mixer.music.get_busy() and not self.stop_flag:
                    pygame.time.Clock().tick(10)
                    
            # 循环播放杜喵音效
            loop_path = self._get_sound_path(loop_sound)
            if loop_path and not self.stop_flag:
                print(f"开始循环播放: {loop_path}")
                pygame.mixer.music.load(loop_path)
                pygame.mixer.music.play(-1)  # -1表示循环播放
                
                # 等待停止信号
                while not self.stop_flag:
                    pygame.time.Clock().tick(10)
                    
        except Exception as e:
            print(f"音效播放错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
            except:
                pass
            
    def start_sound_effect(self, action_type: str):
        """开始播放音效"""
        self.stop_sound_effect()  # 先停止之前的音效
        
        if action_type == "preview":
            initial_sound = "ZhengZaiHeCheng.wav"
        elif action_type == "search":
            initial_sound = "ZhengZaiSouSuo.wav"
        else:
            return
            
        self.current_action = action_type
        self.stop_flag = False
        
        # 启动音效播放线程
        self.sound_thread = threading.Thread(
            target=self._play_sound_loop,
            args=(initial_sound, "DuMiao.wav"),
            daemon=True
        )
        self.sound_thread.start()
        
    def stop_sound_effect(self):
        """停止播放音效"""
        self.stop_flag = True
        if self.sound_thread:
            self.sound_thread.join(timeout=1.0)
        self.current_action = None