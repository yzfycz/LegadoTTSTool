#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主界面模块
包含应用程序的主窗口和所有用户界面控件
"""

import wx
import wx.lib.newevent
import threading
import json
import time
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.provider_manager import ProviderManager
from core.tts_client import TTSClient
from core.json_exporter import JSONExporter
from core.network_scanner import NetworkScanner
from utils.file_utils import FileUtils
from utils.accessibility import AccessibilityUtils
from ui.events import RoleUpdateEvent, EVT_ROLE_UPDATE, ScanCompleteEvent, EVT_SCAN_COMPLETE, ProviderUpdateEvent, EVT_PROVIDER_UPDATE


class MainFrame(wx.Frame):
    """主窗口类"""
    
    def __init__(self, parent, title):
        """初始化主窗口"""
        super().__init__(parent, title=title, size=(900, 700))
        
        # 初始化管理器
        self.provider_manager = ProviderManager()
        self.tts_client = TTSClient()
        self.json_exporter = JSONExporter()
        self.network_scanner = NetworkScanner()
        self.accessibility = AccessibilityUtils()
        
        # 当前选中的角色列表
        self.current_roles = []
        self.selected_roles = set()
        
        # 播报防抖控制
        self.last_announcement_time = {}
        self.announcement_delay = 200  # 毫秒
        
        # 播放状态控制
        self.is_playing = False
        self.is_loading = False
        self.current_request_thread = None
        
        # 绑定自定义事件
        self.Bind(EVT_ROLE_UPDATE, self.on_role_update)
        self.Bind(EVT_SCAN_COMPLETE, self.on_scan_complete)
        self.Bind(EVT_PROVIDER_UPDATE, self.on_provider_update)
        
        # 初始化日志系统
        from utils.logger import get_logger
        self.logger = get_logger()
        
        # 初始化界面
        self._init_ui()
        self._setup_menu()
        self._setup_accessibility()
        
        # 加载配置
        self._load_config()
    
    def _init_ui(self):
        """初始化用户界面"""
        # 创建主面板
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 顶部控制区域
        top_sizer = self._create_top_controls(panel)
        main_sizer.Add(top_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 角色列表区域
        role_sizer = self._create_role_list(panel)
        main_sizer.Add(role_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        # 试听控制区域
        preview_sizer = self._create_preview_controls(panel)
        main_sizer.Add(preview_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        # 底部按钮区域
        button_sizer = self._create_bottom_buttons(panel)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
        # 设置焦点
        self.provider_combo.SetFocus()
    
    def _create_top_controls(self, parent):
        """创建顶部控制区域"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 提供商选择组合框
        provider_label = wx.StaticText(parent, label="方案选择(&S):")
        self.provider_combo = wx.ComboBox(
            parent, 
            choices=[],
            style=wx.CB_READONLY
        )
        self.provider_combo.Bind(wx.EVT_COMBOBOX, self.on_provider_changed)
        
        # 刷新按钮
        self.refresh_button = wx.Button(parent, label="刷新语音角色(&R)")
        self.refresh_button.Bind(wx.EVT_BUTTON, self.on_refresh_roles)
        
        # 添加到sizer
        sizer.Add(provider_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        sizer.Add(self.provider_combo, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        sizer.Add(self.refresh_button, 0, wx.ALIGN_CENTER_VERTICAL)
        
        return sizer
    
    def _create_role_list(self, parent):
        """创建角色列表区域"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 角色列表标签
        list_label = wx.StaticText(parent, label="语音角色(&L)：")
        sizer.Add(list_label, 0, wx.LEFT | wx.TOP, 5)
        
        # 角色列表
        self.role_list = wx.CheckListBox(parent, choices=[], style=wx.LB_SINGLE)
        self.role_list.Bind(wx.EVT_CHECKLISTBOX, self.on_role_selected)
        self.role_list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_role_double_click)
        self.role_list.Bind(wx.EVT_KEY_DOWN, self.on_role_key_down)
        
        sizer.Add(self.role_list, 1, wx.EXPAND | wx.TOP, 5)
        
        return sizer
    
    def _create_preview_controls(self, parent):
        """创建试听控制区域"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 试听文本标签
        preview_label = wx.StaticText(parent, label="语音试听文本(&X):")
        sizer.Add(preview_label, 0, wx.LEFT | wx.TOP, 5)
        
        # 试听文本框
        self.preview_text = wx.TextCtrl(
            parent, 
            value="这是一段默认的试听文本，用户可以编辑这个文本来测试语音合成效果。",
            style=wx.TE_MULTILINE | wx.TE_RICH2
        )
        self.preview_text.SetMinSize((-1, 80))
        sizer.Add(self.preview_text, 0, wx.EXPAND | wx.TOP, 5)
        
        # 参数控制区域
        param_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 语速控制 - 使用TextCtrl
        speed_sizer = wx.BoxSizer(wx.HORIZONTAL)
        speed_label = wx.StaticText(parent, label="语速(&P):")
        self.speed_text = wx.TextCtrl(
            parent,
            value="1.0",
            size=(60, -1),
            style=wx.TE_PROCESS_ENTER | wx.TE_RIGHT
        )
        
        # 设置控件名称和提示
        self.speed_text.SetName("语速")
        self.speed_text.SetHelpText("语速控制，范围0.5-2.0，使用上下键调节，支持直接输入")
        
        # 绑定事件
        self.speed_text.Bind(wx.EVT_TEXT, self.on_speed_text_changed)
        self.speed_text.Bind(wx.EVT_TEXT_ENTER, self.on_speed_text_enter)
        self.speed_text.Bind(wx.EVT_KEY_DOWN, self.on_speed_key_down)
        
        speed_sizer.Add(speed_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        speed_sizer.Add(self.speed_text, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # 音量控制 - 使用TextCtrl
        volume_sizer = wx.BoxSizer(wx.HORIZONTAL)
        volume_label = wx.StaticText(parent, label="音量(&V):")
        self.volume_text = wx.TextCtrl(
            parent,
            value="1.0",
            size=(60, -1),
            style=wx.TE_PROCESS_ENTER | wx.TE_RIGHT
        )
        
        # 设置控件名称和提示
        self.volume_text.SetName("音量")
        self.volume_text.SetHelpText("音量控制，范围0.5-2.0，使用上下键调节，支持直接输入")
        
        # 绑定事件
        self.volume_text.Bind(wx.EVT_TEXT, self.on_volume_text_changed)
        self.volume_text.Bind(wx.EVT_TEXT_ENTER, self.on_volume_text_enter)
        self.volume_text.Bind(wx.EVT_KEY_DOWN, self.on_volume_key_down)
        
        volume_sizer.Add(volume_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        volume_sizer.Add(self.volume_text, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # 试听按钮
        self.preview_button = wx.Button(parent, label="试听选中角色(&T)")
        self.preview_button.Bind(wx.EVT_BUTTON, self.on_preview_button)
        
        # 停止按钮
        self.stop_button = wx.Button(parent, label="停止播放(&O)")
        self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop_button)
        self.stop_button.Enable(False)  # 初始禁用
        
        param_sizer.Add(speed_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)
        param_sizer.Add(volume_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)
        param_sizer.Add(self.preview_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        param_sizer.Add(self.stop_button, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sizer.Add(param_sizer, 0, wx.EXPAND | wx.TOP, 10)
        
        return sizer
    
    def _create_bottom_buttons(self, parent):
        """创建底部按钮区域"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 全选按钮
        self.select_all_button = wx.Button(parent, label="全选(&A)")
        self.select_all_button.Bind(wx.EVT_BUTTON, self.on_select_all)
        
        # 反选按钮
        self.select_inverse_button = wx.Button(parent, label="反选(&D)")
        self.select_inverse_button.Bind(wx.EVT_BUTTON, self.on_select_inverse)
        
        # 导出按钮
        self.export_button = wx.Button(parent, label="导出为JSON(&E)")
        self.export_button.Bind(wx.EVT_BUTTON, self.on_export_json)
        
        # 添加到sizer
        sizer.Add(self.select_all_button, 0, wx.RIGHT, 10)
        sizer.Add(self.select_inverse_button, 0, wx.RIGHT, 10)
        sizer.Add(self.export_button, 1, wx.EXPAND)
        
        return sizer
    
    def _setup_menu(self):
        """设置菜单栏"""
        menubar = wx.MenuBar()
        
        # 操作菜单
        operation_menu = wx.Menu()
        
        # 方案管理菜单项
        provider_manage_item = operation_menu.Append(
            wx.ID_ANY, 
            "方案管理\tM", 
            "管理TTS方案配置"
        )
        self.Bind(wx.EVT_MENU, self.on_provider_manage, provider_manage_item)
        
        operation_menu.AppendSeparator()
        
        # 调试模式菜单项
        debug_mode_item = operation_menu.AppendCheckItem(
            wx.ID_ANY, 
            "调试模式\tD", 
            "开启/关闭调试日志"
        )
        self.Bind(wx.EVT_MENU, self.on_debug_mode, debug_mode_item)
        
        # 查看日志菜单项
        view_log_item = operation_menu.Append(
            wx.ID_ANY, 
            "查看日志\tL", 
            "打开日志文件所在目录"
        )
        self.Bind(wx.EVT_MENU, self.on_view_log, view_log_item)
        
        operation_menu.AppendSeparator()
        
        # 帮助菜单项
        help_item = operation_menu.Append(
            wx.ID_ANY, 
            "帮助\tH", 
            "打开帮助文档"
        )
        self.Bind(wx.EVT_MENU, self.on_help, help_item)
        
        # 关于菜单项
        about_item = operation_menu.Append(
            wx.ID_ANY, 
            "关于\tA", 
            "关于本程序"
        )
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        
        operation_menu.AppendSeparator()
        
        # 退出菜单项
        exit_item = operation_menu.Append(
            wx.ID_ANY, 
            "退出\tE", 
            "退出程序"
        )
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        
        menubar.Append(operation_menu, "操作(&C)")
        
        self.SetMenuBar(menubar)
        
        # 绑定Alt+F4退出
        self.Bind(wx.EVT_CLOSE, self.on_exit)
    
    def _setup_accessibility(self):
        """设置无障碍支持"""
        try:
            # 为控件设置无障碍名称
            self.accessibility.set_control_name(self.provider_combo, "方案选择")
            self.accessibility.set_control_name(self.refresh_button, "刷新语音角色按钮")
            self.accessibility.set_control_name(self.role_list, "语音角色")
            self.accessibility.set_control_name(self.preview_text, "语音试听文本")
            # 文本框已设置名称，无需额外设置
            self.accessibility.set_control_name(self.preview_button, "试听按钮")
            self.accessibility.set_control_name(self.select_all_button, "全选按钮")
            self.accessibility.set_control_name(self.select_inverse_button, "反选按钮")
            self.accessibility.set_control_name(self.export_button, "导出按钮")
            
        except Exception as e:
            print(f"无障碍设置失败: {e}")
    
    def _load_config(self):
        """加载配置"""
        try:
            # 加载方案列表
            providers = self.provider_manager.get_all_providers()
            provider_names = []
            
            for provider in providers:
                if provider.get('enabled', True):
                    custom_name = provider.get('custom_name', '')
                    provider_type = provider.get('type', '')
                    
                    if custom_name and provider_type:
                        name = f"{custom_name} - {provider_type}"
                    elif custom_name:
                        name = custom_name
                    elif provider_type:
                        name = provider_type
                    else:
                        name = "未知提供商"
                    
                    provider_names.append(name)
            
            self.provider_combo.SetItems(provider_names)
            if provider_names:
                self.provider_combo.SetSelection(0)
                self.on_provider_changed(None)
                
        except Exception as e:
            wx.MessageBox(f"加载配置失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    # 事件处理方法
    def on_provider_changed(self, event):
        """方案选择改变事件"""
        try:
            # 清空当前角色列表
            self.role_list.Clear()
            self.current_roles = []
            self.selected_roles = set()
            
            # 获取当前选择的方案
            provider_name = self.provider_combo.GetValue()
            if not provider_name:
                # 更新按钮状态
                self._update_button_states()
                return
            
            # 获取方案配置
            provider = self.provider_manager.get_provider_by_name(provider_name)
            if not provider:
                wx.MessageBox("未找到方案配置", "错误", wx.OK | wx.ICON_ERROR)
                # 更新按钮状态
                self._update_button_states()
                return
            
            # 更新按钮状态，但不自动刷新角色列表
            self._update_button_states()
                
        except Exception as e:
            print(f"切换方案失败: {e}")
            self._update_button_states()
    
    def on_refresh_roles(self, event):
        """刷新角色列表"""
        try:
            # 获取当前选择的方案
            provider_name = self.provider_combo.GetValue()
            if not provider_name:
                wx.MessageBox("请先选择一个方案", "提示", wx.OK | wx.ICON_INFORMATION)
                return
            
            # 获取方案配置
            provider = self.provider_manager.get_provider_by_name(provider_name)
            if not provider:
                wx.MessageBox("未找到方案配置", "错误", wx.OK | wx.ICON_ERROR)
                return
            
            # 清空当前角色列表
            self.role_list.Clear()
            self.current_roles = []
            self.selected_roles = set()
            
            # 添加状态提示
            self.role_list.Append("正在获取音色...")
            
            # 不禁用按钮以保持快捷键功能，只改变标签显示状态
            self.refresh_button.SetLabel("正在刷新...")
            
            # 在后台线程中刷新角色
            threading.Thread(
                target=self._refresh_roles_thread,
                args=(provider,),
                daemon=True
            ).start()
            
        except Exception as e:
            wx.MessageBox(f"刷新角色失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            # 恢复按钮标签
            self.refresh_button.SetLabel("刷新语音角色(&R)")
    
    def _refresh_roles_thread(self, provider):
        """在后台线程中刷新角色列表"""
        try:
            # 获取角色列表
            roles = self.tts_client.get_roles(provider)
            
            # 发送更新事件
            evt = RoleUpdateEvent(roles=roles)
            wx.PostEvent(self, evt)
            
        except Exception as e:
            # 发送错误事件
            evt = RoleUpdateEvent(error=str(e))
            wx.PostEvent(self, evt)
    
    def on_role_update(self, event):
        """角色更新事件处理"""
        # 恢复按钮标签
        self.refresh_button.SetLabel("刷新语音角色(&R)")
        
        if hasattr(event, 'error'):
            wx.MessageBox(f"获取角色列表失败: {event.error}", "错误", wx.OK | wx.ICON_ERROR)
            return
        
        # 过滤掉"使用参考音频"项
        filtered_roles = [role for role in event.roles if role != "使用参考音频"]
        
        # 更新角色列表
        self.current_roles = filtered_roles
        self.role_list.Clear()
        self.selected_roles = set()
        
        # 添加过滤后的角色到列表
        for role in filtered_roles:
            self.role_list.Append(role)
        
        # 更新按钮状态
        self._update_button_states()
        
        # 恢复刷新按钮标签
        self.refresh_button.SetLabel("刷新语音角色(&R)")
        
        # 成功时不显示弹窗，直接显示结果
    
    def on_role_selected(self, event):
        """角色选择事件"""
        index = event.GetInt()
        if self.role_list.IsChecked(index):
            self.selected_roles.add(self.current_roles[index])
        else:
            self.selected_roles.discard(self.current_roles[index])
        
        self._update_button_states()
    
    def on_role_double_click(self, event):
        """角色双击事件"""
        self._preview_selected_role()
    
    def on_role_key_down(self, event):
        """角色列表键盘事件"""
        keycode = event.GetKeyCode()
        
        if keycode == wx.WXK_RETURN:
            # 回车键试听
            self._preview_selected_role()
        elif keycode == wx.WXK_SPACE:
            # 空格键切换选择状态
            index = self.role_list.GetSelection()
            if index != wx.NOT_FOUND:
                self.role_list.Check(index, not self.role_list.IsChecked(index))
                if self.role_list.IsChecked(index):
                    self.selected_roles.add(self.current_roles[index])
                else:
                    self.selected_roles.discard(self.current_roles[index])
                self._update_button_states()
        else:
            event.Skip()
    
    def _slider_to_value(self, slider_pos):
        """将滑动条位置转换为实际数值 (0-15 -> 0.5-2.0)"""
        return slider_pos * 0.1 + 0.5
    
    def _value_to_slider(self, value):
        """将实际数值转换为滑动条位置 (0.5-2.0 -> 0-15)"""
        return int((value - 0.5) / 0.1)
    
    def _validate_and_format_value(self, text_str, control_type):
        """验证并格式化输入值
        
        Args:
            text_str: 输入的文本
            control_type: 控件类型（"语速"或"音量"）
            
        Returns:
            (valid, formatted_value): (是否有效, 格式化后的值)
        """
        try:
            # 尝试转换为浮点数
            value = float(text_str)
            
            # 检查范围
            if 0.5 <= value <= 2.0:
                # 格式化为一位小数
                formatted = f"{value:.1f}"
                return (True, formatted)
            else:
                # 超出范围，修正到最近的有效值
                if value < 0.5:
                    corrected = "0.5"
                else:
                    corrected = "2.0"
                return (False, corrected)
        except (ValueError, TypeError):
            # 转换失败，恢复默认值
            return (False, "1.0")
    
    def _should_announce(self, control_name, current_value):
        """检查是否应该播报（防抖控制）"""
        import time
        current_time = time.time() * 1000  # 转换为毫秒
        
        key = f"{control_name}_{current_value}"
        last_time = self.last_announcement_time.get(key, 0)
        
        if current_time - last_time >= self.announcement_delay:
            self.last_announcement_time[key] = current_time
            return True
        return False
    
    def _announce_value_change(self, control_type, value):
        """播报数值变化"""
        if self._should_announce(control_type, value):
            announcement = f"{control_type} {value:.1f}"
            self.accessibility.announce_to_screen_reader(announcement)
    
    def on_speed_text_changed(self, event):
        """语速文本改变事件"""
        # 这个事件在每次按键时触发，我们在这里进行验证
        text_str = self.speed_text.GetValue()
        
        # 如果输入为空，暂时不做验证
        if not text_str.strip():
            return
        
        # 验证并格式化输入
        valid, formatted = self._validate_and_format_value(text_str, "语速")
        
        # 如果无效，需要修正
        if not valid:
            # 使用CallAfter避免在事件处理中修改控件
            wx.CallAfter(self.speed_text.SetValue, formatted)
            wx.CallAfter(self.speed_text.SetInsertionPointEnd)
        
        # 播报数值变化
        try:
            value = float(formatted)
            self._announce_value_change("语速", value)
        except (ValueError, TypeError):
            pass
        
        event.Skip()
    
    def on_speed_text_enter(self, event):
        """语速文本按Enter键事件"""
        text_str = self.speed_text.GetValue()
        
        # 验证并格式化输入
        valid, formatted = self._validate_and_format_value(text_str, "语速")
        
        # 更新控件值
        self.speed_text.SetValue(formatted)
        self.speed_text.SetInsertionPointEnd()
        
        # 播报最终值
        try:
            value = float(formatted)
            self._announce_value_change("语速", value)
        except (ValueError, TypeError):
            pass
        
        event.Skip()
    
    def on_speed_key_down(self, event):
        """语速键盘按键事件"""
        key_code = event.GetKeyCode()
        
        # 处理上下键
        if key_code == wx.WXK_UP:
            # 增加数值
            current_text = self.speed_text.GetValue()
            try:
                current_value = float(current_text)
                new_value = min(2.0, current_value + 0.1)
                new_text = f"{new_value:.1f}"
                self.speed_text.SetValue(new_text)
                self.speed_text.SetInsertionPointEnd()
                self._announce_value_change("语速", new_value)
            except (ValueError, TypeError):
                self.speed_text.SetValue("1.0")
                self.speed_text.SetInsertionPointEnd()
                self._announce_value_change("语速", 1.0)
            event.Skip(False)  # 阻止默认处理
            return
        
        elif key_code == wx.WXK_DOWN:
            # 减少数值
            current_text = self.speed_text.GetValue()
            try:
                current_value = float(current_text)
                new_value = max(0.5, current_value - 0.1)
                new_text = f"{new_value:.1f}"
                self.speed_text.SetValue(new_text)
                self.speed_text.SetInsertionPointEnd()
                self._announce_value_change("语速", new_value)
            except (ValueError, TypeError):
                self.speed_text.SetValue("1.0")
                self.speed_text.SetInsertionPointEnd()
                self._announce_value_change("语速", 1.0)
            event.Skip(False)  # 阻止默认处理
            return
        
        event.Skip()
    
    def on_volume_text_changed(self, event):
        """音量文本改变事件"""
        # 这个事件在每次按键时触发，我们在这里进行验证
        text_str = self.volume_text.GetValue()
        
        # 如果输入为空，暂时不做验证
        if not text_str.strip():
            return
        
        # 验证并格式化输入
        valid, formatted = self._validate_and_format_value(text_str, "音量")
        
        # 如果无效，需要修正
        if not valid:
            # 使用CallAfter避免在事件处理中修改控件
            wx.CallAfter(self.volume_text.SetValue, formatted)
            wx.CallAfter(self.volume_text.SetInsertionPointEnd)
        
        # 播报数值变化
        try:
            value = float(formatted)
            self._announce_value_change("音量", value)
        except (ValueError, TypeError):
            pass
        
        event.Skip()
    
    def on_volume_text_enter(self, event):
        """音量文本按Enter键事件"""
        text_str = self.volume_text.GetValue()
        
        # 验证并格式化输入
        valid, formatted = self._validate_and_format_value(text_str, "音量")
        
        # 更新控件值
        self.volume_text.SetValue(formatted)
        self.volume_text.SetInsertionPointEnd()
        
        # 播报最终值
        try:
            value = float(formatted)
            self._announce_value_change("音量", value)
        except (ValueError, TypeError):
            pass
        
        event.Skip()
    
    def on_volume_key_down(self, event):
        """音量键盘按键事件"""
        key_code = event.GetKeyCode()
        
        # 处理上下键
        if key_code == wx.WXK_UP:
            # 增加数值
            current_text = self.volume_text.GetValue()
            try:
                current_value = float(current_text)
                new_value = min(2.0, current_value + 0.1)
                new_text = f"{new_value:.1f}"
                self.volume_text.SetValue(new_text)
                self.volume_text.SetInsertionPointEnd()
                self._announce_value_change("音量", new_value)
            except (ValueError, TypeError):
                self.volume_text.SetValue("1.0")
                self.volume_text.SetInsertionPointEnd()
                self._announce_value_change("音量", 1.0)
            event.Skip(False)  # 阻止默认处理
            return
        
        elif key_code == wx.WXK_DOWN:
            # 减少数值
            current_text = self.volume_text.GetValue()
            try:
                current_value = float(current_text)
                new_value = max(0.5, current_value - 0.1)
                new_text = f"{new_value:.1f}"
                self.volume_text.SetValue(new_text)
                self.volume_text.SetInsertionPointEnd()
                self._announce_value_change("音量", new_value)
            except (ValueError, TypeError):
                self.volume_text.SetValue("1.0")
                self.volume_text.SetInsertionPointEnd()
                self._announce_value_change("音量", 1.0)
            event.Skip(False)  # 阻止默认处理
            return
        
        event.Skip()
    
    def on_preview_button(self, event):
        """试听按钮事件"""
        self._preview_selected_role()
    
    def on_select_all(self, event):
        """全选按钮事件"""
        for i in range(len(self.current_roles)):
            self.role_list.Check(i, True)
        
        self.selected_roles = set(self.current_roles)
        self._update_button_states()
    
    def on_select_inverse(self, event):
        """反选按钮事件"""
        new_selection = set()
        
        for i in range(len(self.current_roles)):
            is_checked = self.role_list.IsChecked(i)
            self.role_list.Check(i, not is_checked)
            if not is_checked:
                new_selection.add(self.current_roles[i])
        
        self.selected_roles = new_selection
        self._update_button_states()
    
    def on_export_json(self, event):
        """导出JSON事件"""
        try:
            if not self.selected_roles:
                wx.MessageBox("请先选择要导出的角色", "提示", wx.OK | wx.ICON_INFORMATION)
                return
            
            # 获取当前方案配置
            provider_name = self.provider_combo.GetValue()
            provider = self.provider_manager.get_provider_by_name(provider_name)
            
            if not provider:
                wx.MessageBox("未找到方案配置", "错误", wx.OK | wx.ICON_ERROR)
                return
            
            # 选择保存文件
            with wx.FileDialog(
                self, 
                "保存JSON文件",
                wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            ) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return
                
                pathname = fileDialog.GetPath()
                if not pathname:
                    return
                
                # 生成JSON数据
                json_data = self.json_exporter.generate_json(
                    self.selected_roles,
                    provider,
                    float(self.speed_text.GetValue()),
                    float(self.volume_text.GetValue())
                )
                
                # 保存文件
                with open(pathname, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                
                wx.MessageBox(f"成功导出 {len(self.selected_roles)} 个角色到文件", "成功", wx.OK | wx.ICON_INFORMATION)
                
        except Exception as e:
            wx.MessageBox(f"导出失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def on_provider_manage(self, event):
        """方案管理事件"""
        try:
            from ui.provider_dialog import ProviderDialog
            
            dialog = ProviderDialog(self)
            dialog.ShowModal()
            dialog.Destroy()
            
        except Exception as e:
            wx.MessageBox(f"打开方案管理失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def on_debug_mode(self, event):
        """调试模式切换事件"""
        try:
            # 获取菜单项
            menu_item = event.GetEventObject()
            is_checked = menu_item.IsChecked()
            
            # 设置调试模式
            self.logger.set_debug_mode(is_checked)
            
            status = "开启" if is_checked else "关闭"
            wx.MessageBox(f"调试模式已{status}", "提示", wx.OK | wx.ICON_INFORMATION)
            
            self.logger.log_ui_event("调试模式切换", f"调试模式{status}")
            
        except Exception as e:
            wx.MessageBox(f"切换调试模式失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def on_view_log(self, event):
        """查看日志事件"""
        try:
            from utils.logger import get_logger
            logger = get_logger()
            
            # 打开日志目录
            log_dir = logger.log_dir
            if log_dir.exists():
                os.startfile(log_dir)
                self.logger.log_ui_event("查看日志", f"打开日志目录: {log_dir}")
            else:
                wx.MessageBox("日志目录不存在", "提示", wx.OK | wx.ICON_INFORMATION)
                
        except Exception as e:
            wx.MessageBox(f"打开日志目录失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def on_help(self, event):
        """帮助事件"""
        try:
            # 尝试打开README.md文件
            readme_path = Path(__file__).parent.parent / "README.md"
            if readme_path.exists():
                os.startfile(readme_path)
            else:
                wx.MessageBox("未找到帮助文档", "提示", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"打开帮助文档失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def on_about(self, event):
        """关于事件"""
        about_info = wx.adv.AboutDialogInfo()
        about_info.SetName("LegadoTTSTool")
        about_info.SetVersion("1.0.0")
        about_info.SetDescription("一个专为盲人用户设计的语音合成角色管理工具")
        about_info.SetCopyright("(C) 2024")
        about_info.SetWebSite("https://github.com/yzfycz/LegadoTTSTool")
        about_info.AddDeveloper("yzfycz")
        
        wx.adv.AboutBox(about_info)
    
    def on_exit(self, event):
        """退出事件"""
        try:
            # 停止所有正在运行的线程
            self._stop_all_threads()
            
            # 关闭窗口
            self.Destroy()
        except Exception as e:
            print(f"退出时发生错误: {e}")
            # 强制关闭
            try:
                self.Destroy()
            except:
                pass
    
    def _stop_all_threads(self):
        """停止所有正在运行的线程"""
        try:
            # 停止试听相关的线程
            if hasattr(self, 'preview_button'):
                self.preview_button.Enable(True)
                self.preview_button.SetLabel("试听选中角色")
            
            # 清理TTS客户端资源
            if hasattr(self, 'tts_client'):
                self.tts_client = None
            
            # 清理其他管理器
            if hasattr(self, 'provider_manager'):
                self.provider_manager = None
            if hasattr(self, 'json_exporter'):
                self.json_exporter = None
            if hasattr(self, 'network_scanner'):
                self.network_scanner = None
            
        except Exception as e:
            print(f"停止线程时发生错误: {e}")
    
    def on_scan_complete(self, event):
        """网络扫描完成事件"""
        if hasattr(event, 'servers'):
            # 显示扫描结果
            servers = event.servers
            if servers:
                wx.MessageBox(f"找到 {len(servers)} 个服务器", "扫描完成", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("未找到可用的服务器", "扫描完成", wx.OK | wx.ICON_INFORMATION)
    
    def on_provider_update(self, event):
        """方案更新事件处理"""
        try:
            from utils.logger import get_logger
            logger = get_logger()
            
            logger.debug("收到方案更新事件")
            
            # 添加视觉反馈
            print("🔄 收到方案更新事件，正在重新加载方案列表...")
            
            # 记住当前选中的方案名称
            current_provider_name = self.provider_combo.GetValue()
            
            # 清空当前状态 - 这是最关键的！
            self.role_list.Clear()
            self.current_roles = []
            self.selected_roles = set()
            self.is_playing = False
            self.is_loading = False
            
            # 停止任何正在进行的播放
            if hasattr(self, 'current_request_thread') and self.current_request_thread:
                if self.current_request_thread.is_alive():
                    # 不能直接终止线程，但可以设置标志
                    self.is_playing = False
            
            # 重新加载方案列表
            old_count = len(self.provider_combo.GetItems())
            self._load_config()
            new_count = len(self.provider_combo.GetItems())
            
            print(f"🔄 方案列表已重新加载: {old_count} -> {new_count} 个方案")
            
            # 检查之前选中的方案是否还存在
            if current_provider_name:
                items = self.provider_combo.GetItems()
                if current_provider_name in items:
                    # 如果还存在，重新选中
                    index = items.index(current_provider_name)
                    self.provider_combo.SetSelection(index)
                    print(f"🔄 重新选中方案: {current_provider_name}")
                else:
                    # 如果不存在了，清空相关状态
                    print(f"🔄 方案 '{current_provider_name}' 已删除，清空状态")
                    self.provider_combo.SetSelection(-1)
                    self._update_button_states()
                    self.SetStatusText("方案已删除，请选择其他方案")
            
            # 可选：显示一个短暂的状态提示
            self.SetStatusText("方案列表已更新")
            
            logger.debug("方案列表已重新加载")
            
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger()
            logger.error(f"方案更新失败: {e}")
            print(f"❌ 方案更新失败: {e}")
    
    def _preview_selected_role(self):
        """试听选中的角色"""
        try:
            # 获取选中的角色
            index = self.role_list.GetSelection()
            if index == wx.NOT_FOUND:
                wx.MessageBox("请先选择一个角色", "提示", wx.OK | wx.ICON_INFORMATION)
                return
            
            role = self.current_roles[index]
            
            # 获取当前方案配置
            provider_name = self.provider_combo.GetValue()
            provider = self.provider_manager.get_provider_by_name(provider_name)
            
            if not provider:
                wx.MessageBox("未找到方案配置", "错误", wx.OK | wx.ICON_ERROR)
                return
            
            # 获取试听参数
            text = self.preview_text.GetValue()
            speed = float(self.speed_text.GetValue())
            volume = float(self.volume_text.GetValue())
            
            if not text.strip():
                wx.MessageBox("请输入试听文本", "提示", wx.OK | wx.ICON_INFORMATION)
                return
            
            # 不禁用按钮以保持快捷键功能，只改变标签显示状态
            self.preview_button.SetLabel("正在试听...")
            self.stop_button.Enable(True)
            self.is_loading = True
            
            # 在后台线程中试听
            self.current_request_thread = threading.Thread(
                target=self._preview_thread,
                args=(provider, role, text, speed, volume),
                daemon=True
            )
            self.current_request_thread.start()
            
        except Exception as e:
            wx.MessageBox(f"试听失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            # 恢复按钮状态
            self.preview_button.SetLabel("试听选中角色(&T)")
            self.stop_button.Enable(False)
            self.is_playing = False
            self.is_loading = False
    
    def _preview_thread(self, provider, role, text, speed, volume):
        """在后台线程中试听"""
        try:
            # 检查是否已取消
            if not self.is_loading:
                return
            
            # 调用TTS服务
            audio_data = self.tts_client.preview_speech(provider, role, text, speed, volume)
            
            # 检查是否已取消
            if not self.is_loading or not audio_data:
                return
            
            # 开始播放
            self.is_loading = False
            self.is_playing = True
            
            # 播放音频
            self._play_audio(audio_data)
            
        except Exception as e:
            if self.is_loading:  # 只有没有取消时才显示错误
                wx.CallAfter(wx.MessageBox, f"试听失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
        finally:
            # 简单恢复按钮状态，不调用复杂的恢复函数
            wx.CallAfter(self._simple_restore_preview_button)
    
    def _play_audio(self, audio_data):
        """播放音频"""
        try:
            import tempfile
            import pygame
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # 初始化pygame音频
            pygame.mixer.init()
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            # 等待播放完成，检查停止状态
            while pygame.mixer.music.get_busy() and self.is_playing:
                pygame.time.Clock().tick(10)
            
            # 清理资源
            pygame.mixer.quit()
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"音频播放失败: {e}")
        finally:
            self.is_playing = False
    
    def _simple_restore_preview_button(self):
        """简单恢复试听按钮状态（不涉及复杂的焦点管理）"""
        try:
            self.preview_button.SetLabel("试听选中角色(&T)")
            self.stop_button.Enable(False)
            self.is_playing = False
            self.is_loading = False
            print("简单恢复试听按钮状态")
        except Exception as e:
            print(f"简单恢复试听按钮失败: {e}")
    
    def _restore_preview_button(self):
        """恢复试听按钮"""
        # 恢复按钮标签和状态
        self.preview_button.SetLabel("试听选中角色(&T)")
        self.stop_button.Enable(False)
        self.is_playing = False
        self.is_loading = False
    
    def _recreate_refresh_button(self):
        """重新创建刷新按钮以恢复快捷键功能"""
        try:
            # 获取按钮的父容器和sizer
            parent = self.refresh_button.GetParent()
            sizer = self.refresh_button.GetContainingSizer()
            
            if not parent or not sizer:
                print("无法获取按钮的父容器或sizer")
                return
            
            # 保存按钮的原始标签和位置信息
            original_label = "刷新语音角色(&R)"  # 直接使用标准标签
            
            # 查找按钮在sizer中的位置
            index = -1
            for i, child in enumerate(sizer.GetChildren()):
                if child.GetWindow() == self.refresh_button:
                    index = i
                    break
            
            if index == -1:
                print("无法在sizer中找到按钮")
                return
            
            # 保存原有样式和位置信息
            sizer_item = sizer.GetItem(index)
            original_style = sizer_item.GetFlag()
            original_border = sizer_item.GetBorder()
            
            print(f"刷新按钮原始位置: {index}")
            print(f"刷新按钮原始样式: flag={original_style}, border={original_border}")
            
            # 先从sizer中移除旧按钮
            sizer.Remove(index)
            
            # 销毁旧按钮
            self.refresh_button.Destroy()
            
            # 创建新按钮
            self.refresh_button = wx.Button(parent, label=original_label)
            self.refresh_button.Bind(wx.EVT_BUTTON, self.on_refresh_roles)
            
            # 使用原有样式添加到sizer中
            sizer.Insert(index, self.refresh_button, original_style, original_border)
            
            # 重新布局
            sizer.Layout()
            parent.Layout()
            
            # 修复键盘导航顺序 - 将新按钮移动到正确的Tab顺序位置
            self._fix_tab_order(parent, self.refresh_button, index)
            
            print(f"刷新按钮重新创建成功，位置: {index}")
            
        except Exception as e:
            print(f"重新创建刷新按钮失败: {e}")
            # 如果重新创建失败，尝试简单恢复标签
            if hasattr(self, 'refresh_button'):
                try:
                    self.refresh_button.SetLabel("刷新语音角色(&R)")
                except:
                    pass
    
    def _recreate_preview_button(self):
        """重新创建试听按钮以恢复快捷键功能"""
        try:
            # 获取按钮的父容器和sizer
            parent = self.preview_button.GetParent()
            sizer = self.preview_button.GetContainingSizer()
            
            if not parent or not sizer:
                print("无法获取试听按钮的父容器或sizer")
                return
            
            # 保存按钮的原始标签
            original_label = "试听选中角色(&T)"  # 直接使用标准标签
            
            # 查找按钮在sizer中的位置
            index = -1
            for i, child in enumerate(sizer.GetChildren()):
                if child.GetWindow() == self.preview_button:
                    index = i
                    break
            
            if index == -1:
                print("无法在sizer中找到试听按钮")
                return
            
            # 保存原有样式和位置信息
            sizer_item = sizer.GetItem(index)
            original_style = sizer_item.GetFlag()
            original_border = sizer_item.GetBorder()
            
            print(f"试听按钮原始位置: {index}")
            print(f"试听按钮原始样式: flag={original_style}, border={original_border}")
            
            # 先从sizer中移除旧按钮
            sizer.Remove(index)
            
            # 销毁旧按钮
            self.preview_button.Destroy()
            
            # 创建新按钮
            self.preview_button = wx.Button(parent, label=original_label)
            self.preview_button.Bind(wx.EVT_BUTTON, self.on_preview_button)
            
            # 使用原有样式添加到sizer中
            sizer.Insert(index, self.preview_button, original_style, original_border)
            
            # 重新布局
            sizer.Layout()
            parent.Layout()
            
            # 修复键盘导航顺序 - 将新按钮移动到正确的Tab顺序位置
            self._fix_tab_order(parent, self.preview_button, index)
            
            print(f"试听按钮重新创建成功，位置: {index}")
            
        except Exception as e:
            print(f"重新创建试听按钮失败: {e}")
            # 如果重新创建失败，尝试简单恢复标签
            if hasattr(self, 'preview_button'):
                try:
                    self.preview_button.SetLabel("试听选中角色(&T)")
                except:
                    pass
    
    def _fix_tab_order(self, parent, new_button, desired_sizer_index):
        """修复按钮的键盘导航顺序 - 使用更简单的方法"""
        try:
            # 获取父容器中的所有子控件，保持sizer顺序
            children = parent.GetChildren()
            
            # 按照sizer中的顺序找到所有按钮控件
            button_windows = []
            for child in children:
                window = child.GetWindow()
                if window and isinstance(window, wx.Button) and window.IsShown():
                    button_windows.append(window)
            
            # 找到新按钮在按钮列表中的位置
            current_button_pos = -1
            for i, button in enumerate(button_windows):
                if button == new_button:
                    current_button_pos = i
                    break
            
            # 如果新按钮不在期望的位置，调整Tab顺序
            if current_button_pos != desired_sizer_index and current_button_pos != -1:
                # 简单策略：将按钮按照sizer顺序重新排列Tab顺序
                if desired_sizer_index < len(button_windows):
                    if desired_sizer_index > 0:
                        # 移动到指定按钮的后面
                        target_button = button_windows[desired_sizer_index - 1]
                        new_button.MoveAfterInTabOrder(target_button)
                    else:
                        # 移动到第一个按钮的前面
                        first_button = button_windows[0]
                        new_button.MoveBeforeInTabOrder(first_button)
                    
                    print(f"已调整按钮Tab顺序从位置 {current_button_pos} 到 {desired_sizer_index}")
            
        except Exception as e:
            print(f"修复Tab顺序失败: {e}")
    
    def _save_current_focus(self):
        """保存当前焦点控件"""
        try:
            focused_window = self.FindFocus()
            if focused_window:
                self._last_focused_window = focused_window
                print(f"已保存当前焦点: {focused_window.GetName() if hasattr(focused_window, 'GetName') else 'Unknown'}")
        except Exception as e:
            print(f"保存焦点失败: {e}")
    
    def _restore_saved_focus(self):
        """恢复之前保存的焦点"""
        try:
            if hasattr(self, '_last_focused_window') and self._last_focused_window:
                # 检查控件是否还存在且可见
                if self._last_focused_window.IsShown():
                    self._last_focused_window.SetFocus()
                    print("已恢复之前保存的焦点")
                    return True
                else:
                    print("之前聚焦的控件已不可见")
            return False
        except Exception as e:
            print(f"恢复焦点失败: {e}")
            return False
    
    def _reset_button_shortcuts(self):
        """重置按钮快捷键功能的简单方法"""
        try:
            # 只恢复按钮标签，不涉及焦点管理
            if hasattr(self, 'refresh_button'):
                self.refresh_button.SetLabel("刷新语音角色(&R)")
            
            if hasattr(self, 'preview_button'):
                self.preview_button.SetLabel("试听选中角色(&T)")
            
        except Exception as e:
            print(f"重置按钮快捷键失败: {e}")
    
    def on_preview_button(self, event):
        """试听按钮事件"""
        self._preview_selected_role()
    
    def on_stop_button(self, event):
        """停止按钮事件"""
        try:
            if self.is_playing:
                # 停止pygame播放
                try:
                    import pygame
                    if pygame.mixer.get_init():
                        pygame.mixer.music.stop()
                        pygame.mixer.quit()
                except:
                    pass
                self.is_playing = False
                
            if self.is_loading:
                # 取消正在进行的请求
                self.is_loading = False
                
            # 恢复按钮状态
            self.preview_button.SetLabel("试听选中角色(&T)")
            self.stop_button.Enable(False)
            
        except Exception as e:
            print(f"停止播放失败: {e}")
            # 确保按钮状态恢复
            self.preview_button.SetLabel("试听选中角色(&T)")
            self.stop_button.Enable(False)
            self.is_playing = False
            self.is_loading = False
    
    def _update_button_states(self):
        """更新按钮状态"""
        has_selection = len(self.selected_roles) > 0
        has_roles = len(self.current_roles) > 0
        
        self.select_all_button.Enable(has_roles)
        self.select_inverse_button.Enable(has_roles)
        self.export_button.Enable(has_selection)
        self.preview_button.Enable(has_roles)