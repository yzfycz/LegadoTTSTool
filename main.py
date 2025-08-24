#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LegadoTTSTool - 语音合成角色导出工具
主程序入口
"""

import wx
import os
import sys
import json
import time
import threading
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_frame import MainFrame
from core.provider_manager import ProviderManager
from utils.file_utils import FileUtils
from utils.accessibility import AccessibilityUtils

class LegadoTTSApp(wx.App):
    """LegadoTTS应用程序主类"""
    
    def OnInit(self):
        """初始化应用程序"""
        try:
            # 设置应用程序名称
            self.SetAppName("LegadoTTSTool")
            
            # 创建必要的目录
            self._create_directories()
            
            # 初始化提供商会管理器
            self.provider_manager = ProviderManager()
            
            # 创建主窗口
            self.frame = MainFrame(None, title="LegadoTTSTool - 语音合成角色导出工具")
            self.frame.Centre()
            self.frame.Show()
            
            # 设置无障碍支持
            self._setup_accessibility()
            
            return True
            
        except Exception as e:
            wx.MessageBox(f"程序初始化失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            return False
    
    def _create_directories(self):
        """创建必要的目录结构"""
        directories = [
            "config",
            "exports",
            "logs",
            "temp"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _setup_accessibility(self):
        """设置无障碍支持"""
        try:
            # 启用屏幕阅读器支持
            accessibility = AccessibilityUtils()
            accessibility.setup_global_accessibility()
        except Exception as e:
            print(f"无障碍设置失败: {e}")

def main():
    """主函数"""
    try:
        # 创建应用程序实例
        app = LegadoTTSApp()
        
        # 运行应用程序
        app.MainLoop()
        
    except KeyboardInterrupt:
        print("程序被用户中断")
    except Exception as e:
        print(f"程序运行错误: {e}")
        wx.MessageBox(f"程序运行错误: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

if __name__ == "__main__":
    main()