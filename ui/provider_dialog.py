#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案对话框模块
用于管理TTS方案的增删改查操作
"""

import wx
import wx.lib.scrolledpanel
import threading
from typing import List, Dict, Any, Optional

from core.provider_manager import ProviderManager
from core.network_scanner import NetworkScanner
from ui.config_dialog import ConfigDialog

# 创建自定义事件
ProviderUpdateEvent, EVT_PROVIDER_UPDATE = wx.lib.newevent.NewEvent()

class ProviderDialog(wx.Dialog):
    """方案管理对话框"""
    
    def __init__(self, parent):
        """初始化对话框"""
        super().__init__(
            parent, 
            title="方案管理", 
            size=(700, 500),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        # 初始化管理器
        self.provider_manager = ProviderManager()
        self.network_scanner = NetworkScanner()
        
        # 当前选中的方案
        self.selected_provider = None
        
        # 初始化界面
        self._init_ui()
        self._load_providers()
        
        # 居中显示
        self.Centre()
    
    def _send_provider_update_event(self):
        """发送方案更新事件"""
        try:
            event = ProviderUpdateEvent()
            wx.PostEvent(self.GetParent(), event)
        except Exception as e:
            print(f"发送方案更新事件失败: {e}")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 创建主面板
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 方案列表区域
        list_sizer = self._create_provider_list(panel)
        main_sizer.Add(list_sizer, 1, wx.EXPAND | wx.ALL, 10)
        
        # 按钮区域
        button_sizer = self._create_buttons(panel)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        panel.SetSizer(main_sizer)
    
    def _create_provider_list(self, parent):
        """创建方案列表区域"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 标签
        label = wx.StaticText(parent, label="已配置的方案:")
        sizer.Add(label, 0, wx.LEFT | wx.TOP, 5)
        
        # 方案列表
        self.provider_list = wx.ListCtrl(
            parent, 
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        
        # 添加列
        self.provider_list.InsertColumn(0, "显示名称", width=200)
        self.provider_list.InsertColumn(1, "类型", width=100)
        self.provider_list.InsertColumn(2, "服务器地址", width=150)
        self.provider_list.InsertColumn(3, "状态", width=80)
        
        # 绑定事件
        self.provider_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_provider_selected)
        self.provider_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_provider_activated)
        
        sizer.Add(self.provider_list, 1, wx.EXPAND | wx.TOP, 5)
        
        return sizer
    
    def _create_buttons(self, parent):
        """创建按钮区域"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 新建按钮
        self.new_button = wx.Button(parent, label="新建")
        self.new_button.Bind(wx.EVT_BUTTON, self.on_new_provider)
        
        # 编辑按钮
        self.edit_button = wx.Button(parent, label="编辑")
        self.edit_button.Bind(wx.EVT_BUTTON, self.on_edit_provider)
        self.edit_button.Enable(False)
        
        # 删除按钮
        self.delete_button = wx.Button(parent, label="删除")
        self.delete_button.Bind(wx.EVT_BUTTON, self.on_delete_provider)
        self.delete_button.Enable(False)
        
        # 确定按钮
        self.ok_button = wx.Button(parent, label="确定", id=wx.ID_OK)
        
        # 关闭按钮
        self.close_button = wx.Button(parent, label="关闭", id=wx.ID_CANCEL)
        
        # 添加到sizer
        sizer.Add(self.new_button, 0, wx.RIGHT, 10)
        sizer.Add(self.edit_button, 0, wx.RIGHT, 10)
        sizer.Add(self.delete_button, 0, wx.RIGHT, 10)
        sizer.AddStretchSpacer(1)
        sizer.Add(self.ok_button, 0, wx.RIGHT, 10)
        sizer.Add(self.close_button, 0)
        
        return sizer
    
    def _load_providers(self):
        """加载方案列表"""
        try:
            # 清空列表
            self.provider_list.DeleteAllItems()
            
            # 获取所有方案
            providers = self.provider_manager.get_all_providers()
            
            # 添加到列表
            for i, provider in enumerate(providers):
                # 显示名称
                display_name = provider.get('custom_name', provider.get('type', ''))
                
                # 类型
                provider_type = provider.get('type', '')
                
                # 服务器地址
                server_address = provider.get('server_address', '')
                
                # 状态
                status = "启用" if provider.get('enabled', True) else "禁用"
                
                # 添加到列表
                index = self.provider_list.InsertItem(i, display_name)
                self.provider_list.SetItem(index, 1, provider_type)
                self.provider_list.SetItem(index, 2, server_address)
                self.provider_list.SetItem(index, 3, status)
                
                # 保存方案数据
                self.provider_list.SetItemData(index, i)
            
        except Exception as e:
            wx.MessageBox(f"加载方案列表失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def on_provider_selected(self, event):
        """方案选择事件"""
        # 获取选中的索引
        index = event.GetIndex()
        
        if index != -1:
            # 获取方案数据
            provider_data = self.provider_list.GetItemData(index)
            providers = self.provider_manager.get_all_providers()
            
            if provider_data < len(providers):
                self.selected_provider = providers[provider_data]
            else:
                self.selected_provider = None
        else:
            self.selected_provider = None
        
        # 更新按钮状态
        self._update_button_states()
    
    def on_provider_activated(self, event):
        """方案双击事件"""
        self.on_edit_provider(event)
    
    def on_new_provider(self, event):
        """新建方案事件"""
        try:
            # 创建配置对话框
            dialog = ConfigDialog(self, title="新建方案")
            
            if dialog.ShowModal() == wx.ID_OK:
                # 获取配置数据
                config_data = dialog.get_config_data()
                
                # 保存方案
                self.provider_manager.add_provider(config_data)
                
                # 重新加载列表
                self._load_providers()
                
                # 发送方案更新事件
                self._send_provider_update_event()
                
                wx.MessageBox("方案创建成功", "成功", wx.OK | wx.ICON_INFORMATION)
            
            dialog.Destroy()
            
        except Exception as e:
            wx.MessageBox(f"创建方案失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def on_edit_provider(self, event):
        """编辑方案事件"""
        try:
            if not self.selected_provider:
                return
            
            # 创建配置对话框
            dialog = ConfigDialog(self, title="编辑方案", provider=self.selected_provider)
            
            if dialog.ShowModal() == wx.ID_OK:
                # 获取配置数据
                config_data = dialog.get_config_data()
                
                # 更新方案
                provider_id = self.selected_provider.get('id')
                self.provider_manager.update_provider(provider_id, config_data)
                
                # 重新加载列表
                self._load_providers()
                
                # 发送方案更新事件
                self._send_provider_update_event()
                
                wx.MessageBox("方案更新成功", "成功", wx.OK | wx.ICON_INFORMATION)
            
            dialog.Destroy()
            
        except Exception as e:
            wx.MessageBox(f"编辑方案失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def on_delete_provider(self, event):
        """删除方案事件"""
        try:
            if not self.selected_provider:
                return
            
            # 确认删除
            display_name = self.selected_provider.get('custom_name', self.selected_provider.get('type', ''))
            
            result = wx.MessageBox(
                f"确定要删除方案 '{display_name}' 吗？",
                "确认删除",
                wx.YES_NO | wx.ICON_QUESTION
            )
            
            if result == wx.YES:
                # 删除方案
                provider_id = self.selected_provider.get('id')
                self.provider_manager.delete_provider(provider_id)
                
                # 清空选择
                self.selected_provider = None
                
                # 重新加载列表
                self._load_providers()
                
                # 更新按钮状态
                self._update_button_states()
                
                # 发送方案更新事件
                self._send_provider_update_event()
                
                wx.MessageBox("方案删除成功", "成功", wx.OK | wx.ICON_INFORMATION)
            
        except Exception as e:
            wx.MessageBox(f"删除方案失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
        
    def _update_button_states(self):
        """更新按钮状态"""
        has_selection = self.selected_provider is not None
        
        self.edit_button.Enable(has_selection)
        self.delete_button.Enable(has_selection)