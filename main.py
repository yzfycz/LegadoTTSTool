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
            print("正在创建主窗口...")
            self.frame = MainFrame(None, title="LegadoTTSTool - 语音合成角色导出工具")
            self.frame.Centre()
            self.frame.Show()
            print("主窗口创建成功")
            
            # 设置无障碍支持
            print("正在设置无障碍支持...")
            self._setup_accessibility()
            print("无障碍支持设置完成")
            
            return True
            
        except Exception as e:
            import traceback
            print(f"程序初始化失败: {str(e)}")
            print("详细错误信息:")
            traceback.print_exc()
            wx.MessageBox(f"程序初始化失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            return False
    
    def OnExit(self):
        """应用程序退出时的清理工作"""
        try:
            print("应用程序正在退出...")
            
            # 先清理框架
            if hasattr(self, 'frame') and self.frame:
                try:
                    self.frame.Destroy()
                    self.frame = None
                except:
                    pass
            
            # 然后清理管理器
            if hasattr(self, 'provider_manager'):
                self.provider_manager = None
            
        except Exception as e:
            print(f"退出清理失败: {e}")
        
        # 调用父类的退出方法
        return 0
    
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
    app = None
    try:
        # 创建应用程序实例
        app = LegadoTTSApp()
        
        # 运行应用程序
        app.MainLoop()
        
    except KeyboardInterrupt:
        print("程序被用户中断")
    except Exception as e:
        print(f"程序运行错误: {e}")
        try:
            wx.MessageBox(f"程序运行错误: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
        except:
            pass
    finally:
        # 清理资源 - 使用更安全的方式
        if app:
            try:
                # 先尝试退出主循环
                if app.IsMainLoopRunning():
                    app.ExitMainLoop()
                
                # 延迟一下再销毁应用
                import time
                time.sleep(0.1)
                
                # 销毁应用
                app.Destroy()
            except RecursionError:
                print("检测到递归错误，跳过应用销毁")
            except Exception as e:
                print(f"应用销毁失败: {e}")
            finally:
                # 强制退出所有wxPython窗口
                try:
                    wx.GetApp().Exit()
                except:
                    pass

if __name__ == "__main__":
    main()