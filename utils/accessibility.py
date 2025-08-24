#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无障碍工具模块
提供无障碍支持相关的工具函数
"""

import wx
import sys
from typing import Optional, Dict, Any

class AccessibilityUtils:
    """无障碍工具类"""
    
    def __init__(self):
        """初始化无障碍工具"""
        self.screen_reader_enabled = self._detect_screen_reader()
    
    def _detect_screen_reader(self) -> bool:
        """检测屏幕阅读器是否运行"""
        try:
            # Windows屏幕阅读器检测
            if sys.platform == 'win32':
                import win32gui
                import win32con
                
                # 检查常见的屏幕阅读器窗口
                screen_readers = [
                    'NVDA',  # NVDA屏幕阅读器
                    'JAWS',  # JAWS屏幕阅读器
                    'System.Agency',  # Windows讲述人
                    'Freedom Scientific',  # Freedom Scientific产品
                ]
                
                def enum_windows_proc(hwnd, lParam):
                    window_title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    
                    for reader in screen_readers:
                        if reader in window_title or reader in class_name:
                            lParam.append(True)
                            return False
                    
                    return True
                
                found = []
                win32gui.EnumWindows(enum_windows_proc, found)
                return len(found) > 0
            
            # 其他平台的检测可以在这里添加
            return False
            
        except Exception:
            return False
    
    def setup_global_accessibility(self):
        """设置全局无障碍支持"""
        try:
            # 设置wxPython的无障碍模式
            if hasattr(wx, 'GetApp'):
                app = wx.GetApp()
                if app:
                    # 启用无障碍支持
                    app.SetUseBestVisual(True)
                    # 注意：SetAccessibilityMode方法在wxPython中不存在
            
            # 设置系统级无障碍支持
            self._setup_system_accessibility()
            
        except Exception as e:
            print(f"设置全局无障碍失败: {e}")
    
    def _setup_system_accessibility(self):
        """设置系统级无障碍支持"""
        try:
            if sys.platform == 'win32':
                import ctypes
                
                # 启用系统无障碍支持
                SPI_SETSCREENREADER = 0x0047
                ctypes.windll.user32.SystemParametersInfoW(
                    SPI_SETSCREENREADER, 
                    1, 
                    None, 
                    0
                )
                
        except Exception as e:
            print(f"设置系统无障碍失败: {e}")
    
    def set_control_name(self, control: wx.Window, name: str):
        """设置控件的无障碍名称"""
        try:
            if hasattr(control, 'SetName'):
                control.SetName(name)
            
            # 设置控件的Help文本
            if hasattr(control, 'SetHelpText'):
                control.SetHelpText(name)
            
            # 设置控件的描述
            if hasattr(control, 'SetDescription'):
                control.SetDescription(name)
                
        except Exception as e:
            print(f"设置控件名称失败: {e}")
    
    def set_control_accessibility_info(self, control: wx.Window, name: str, description: str = "", help_text: str = ""):
        """设置控件的完整无障碍信息"""
        try:
            # 设置名称
            self.set_control_name(control, name)
            
            # 设置描述
            if description and hasattr(control, 'SetDescription'):
                control.SetDescription(description)
            
            # 设置帮助文本
            if help_text and hasattr(control, 'SetHelpText'):
                control.SetHelpText(help_text)
            
            # 设置控件的Role
            if hasattr(control, 'SetAccessible'):
                accessible = control.GetAccessible()
                if accessible:
                    accessible.SetName(name)
                    if description:
                        accessible.SetDescription(description)
            
        except Exception as e:
            print(f"设置控件无障碍信息失败: {e}")
    
    def announce_to_screen_reader(self, message: str):
        """向屏幕阅读器播报消息"""
        try:
            if self.screen_reader_enabled:
                # 使用wxPython的消息框来触发屏幕阅读器播报
                wx.CallAfter(self._announce_message, message)
            
        except Exception as e:
            print(f"屏幕阅读器播报失败: {e}")
    
    def _announce_message(self, message: str):
        """播报消息的内部方法"""
        try:
            # 创建一个隐藏的消息框来触发播报
            dialog = wx.Dialog(None, style=wx.STAY_ON_TOP | wx.DIALOG_NO_PARENT)
            dialog.SetTitle(message)
            dialog.Show()
            wx.CallLater(100, dialog.Destroy)
            
        except Exception as e:
            print(f"播报消息失败: {e}")
    
    def set_focus_with_announcement(self, control: wx.Window, announcement: str = ""):
        """设置焦点并播报"""
        try:
            # 设置焦点
            control.SetFocus()
            
            # 播报消息
            if announcement:
                self.announce_to_screen_reader(announcement)
            else:
                # 播报控件名称
                name = control.GetName() if hasattr(control, 'GetName') else ""
                if name:
                    self.announce_to_screen_reader(name)
            
        except Exception as e:
            print(f"设置焦点播报失败: {e}")
    
    def get_control_info(self, control: wx.Window) -> Dict[str, Any]:
        """获取控件的无障碍信息"""
        try:
            info = {
                'name': '',
                'description': '',
                'help_text': '',
                'class_name': control.__class__.__name__,
                'enabled': control.IsEnabled(),
                'visible': control.IsShown(),
                'has_focus': control.HasFocus()
            }
            
            # 获取名称
            if hasattr(control, 'GetName'):
                info['name'] = control.GetName()
            
            # 获取描述
            if hasattr(control, 'GetDescription'):
                info['description'] = control.GetDescription()
            
            # 获取帮助文本
            if hasattr(control, 'GetHelpText'):
                info['help_text'] = control.GetHelpText()
            
            # 获取窗口标题
            if hasattr(control, 'GetLabel'):
                info['label'] = control.GetLabel()
            
            # 获取值
            if hasattr(control, 'GetValue'):
                info['value'] = control.GetValue()
            
            return info
            
        except Exception as e:
            print(f"获取控件信息失败: {e}")
            return {}
    
    def setup_keyboard_navigation(self, parent: wx.Window):
        """设置键盘导航"""
        try:
            # 为所有子控件设置键盘导航
            for child in parent.GetChildren():
                self._setup_control_keyboard_navigation(child)
                
        except Exception as e:
            print(f"设置键盘导航失败: {e}")
    
    def _setup_control_keyboard_navigation(self, control: wx.Window):
        """为单个控件设置键盘导航"""
        try:
            # 设置控件可以接收焦点
            if control.AcceptsFocus():
                # 绑定键盘事件
                control.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
                control.Bind(wx.EVT_CHAR, self._on_char)
            
            # 递归设置子控件
            for child in control.GetChildren():
                self._setup_control_keyboard_navigation(child)
                
        except Exception as e:
            print(f"设置控件键盘导航失败: {e}")
    
    def _on_key_down(self, event: wx.KeyEvent):
        """键盘按下事件"""
        try:
            key_code = event.GetKeyCode()
            
            # 处理特殊按键
            if key_code == wx.WXK_F1:
                # F1键显示帮助
                self._show_help_for_control(event.GetEventObject())
                return
            
            event.Skip()
            
        except Exception as e:
            print(f"键盘事件处理失败: {e}")
            event.Skip()
    
    def _on_char(self, event: wx.KeyEvent):
        """字符输入事件"""
        try:
            # 可以在这里处理特定的字符输入
            event.Skip()
            
        except Exception as e:
            print(f"字符事件处理失败: {e}")
            event.Skip()
    
    def _show_help_for_control(self, control: wx.Window):
        """显示控件的帮助信息"""
        try:
            help_text = ""
            
            if hasattr(control, 'GetHelpText'):
                help_text = control.GetHelpText()
            
            if hasattr(control, 'GetName'):
                if not help_text:
                    help_text = control.GetName()
            
            if help_text:
                wx.MessageBox(help_text, "帮助", wx.OK | wx.ICON_INFORMATION)
            
        except Exception as e:
            print(f"显示帮助失败: {e}")
    
    def setup_high_contrast_mode(self, parent: wx.Window):
        """设置高对比度模式"""
        try:
            # 检测系统是否使用高对比度
            if self._is_high_contrast_mode():
                # 调整控件颜色
                self._apply_high_contrast_colors(parent)
                
        except Exception as e:
            print(f"设置高对比度失败: {e}")
    
    def _is_high_contrast_mode(self) -> bool:
        """检测是否使用高对比度模式"""
        try:
            if sys.platform == 'win32':
                import ctypes
                
                HIGHCONTRAST = 0x42
                HCF_HIGHCONTRASTON = 0x01
                
                class HIGHCONTRAST(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", ctypes.c_ulong),
                        ("dwFlags", ctypes.c_ulong),
                        ("lpszDefaultScheme", ctypes.c_wchar_p)
                    ]
                
                hc = HIGHCONTRAST()
                hc.cbSize = ctypes.sizeof(hc)
                
                if ctypes.windll.user32.SystemParametersInfoW(
                    HIGHCONTRAST, 
                    ctypes.sizeof(hc), 
                    ctypes.byref(hc), 
                    0
                ):
                    return (hc.dwFlags & HCF_HIGHCONTRASTON) != 0
            
            return False
            
        except Exception:
            return False
    
    def _apply_high_contrast_colors(self, parent: wx.Window):
        """应用高对比度颜色"""
        try:
            # 设置黑色背景和白色文字
            black = wx.Colour(0, 0, 0)
            white = wx.Colour(255, 255, 255)
            
            for child in parent.GetChildren():
                if hasattr(child, 'SetBackgroundColour'):
                    child.SetBackgroundColour(black)
                if hasattr(child, 'SetForegroundColour'):
                    child.SetForegroundColour(white)
                
                # 递归处理子控件
                self._apply_high_contrast_colors(child)
                
        except Exception as e:
            print(f"应用高对比度颜色失败: {e}")
    
    def get_accessibility_settings(self) -> Dict[str, Any]:
        """获取无障碍设置"""
        try:
            settings = {
                'screen_reader_enabled': self.screen_reader_enabled,
                'high_contrast_mode': self._is_high_contrast_mode(),
                'keyboard_navigation': True,
                'large_text': False,
                'show_captions': False
            }
            
            return settings
            
        except Exception as e:
            print(f"获取无障碍设置失败: {e}")
            return {}
    
    def is_accessibility_enabled(self) -> bool:
        """检查是否启用了无障碍功能"""
        try:
            # 检查屏幕阅读器
            if self.screen_reader_enabled:
                return True
            
            # 检查高对比度
            if self._is_high_contrast_mode():
                return True
            
            # 检查其他无障碍功能
            return False
            
        except Exception:
            return False