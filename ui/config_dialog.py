#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提供商配置对话框模块
用于创建和编辑TTS提供商配置
"""

import wx
import wx.lib.scrolledpanel
import uuid
import time
from typing import Dict, Any, Optional

class ConfigDialog(wx.Dialog):
    """提供商配置对话框"""
    
    def __init__(self, parent, title="配置提供商", provider=None, server_data=None):
        """初始化配置对话框"""
        super().__init__(
            parent, 
            title=title, 
            size=(500, 400),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        # 提供商数据
        self.provider = provider
        self.server_data = server_data
        
        # 配置数据
        self.config_data = {}
        
        # 支持的提供商类型
        self.provider_types = ["index TTS"]
        
        # 初始化界面
        self._init_ui()
        
        # 如果有提供商数据，加载配置
        if provider:
            self._load_provider_config()
        elif server_data:
            self._load_server_config()
        
        # 居中显示
        self.Centre()
    
    def _init_ui(self):
        """初始化用户界面"""
        # 创建滚动面板
        panel = wx.lib.scrolledpanel.ScrolledPanel(self)
        panel.SetupScrolling()
        
        # 创建主sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 基本信息区域
        basic_sizer = self._create_basic_info(panel)
        main_sizer.Add(basic_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 动态配置区域
        self.dynamic_sizer = self._create_dynamic_config(panel)
        main_sizer.Add(self.dynamic_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        # 按钮区域
        button_sizer = self._create_buttons(panel)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
        # 设置初始焦点
        self.type_combo.SetFocus()
    
    def _create_basic_info(self, parent):
        """创建基本信息区域"""
        sizer = wx.StaticBoxSizer(wx.StaticBox(parent, label="基本信息"), wx.VERTICAL)
        
        grid_sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=8, hgap=10)
        grid_sizer.AddGrowableCol(1, 1)
        
        # 提供商类型
        type_label = wx.StaticText(parent, label="提供商类型:")
        self.type_combo = wx.ComboBox(
            parent, 
            choices=self.provider_types,
            style=wx.CB_READONLY
        )
        self.type_combo.Bind(wx.EVT_COMBOBOX, self.on_type_changed)
        
        # 自定义名称
        name_label = wx.StaticText(parent, label="自定义名称:")
        self.name_text = wx.TextCtrl(parent)
        
        # 添加到grid
        grid_sizer.Add(type_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.type_combo, 0, wx.EXPAND)
        grid_sizer.Add(name_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.name_text, 0, wx.EXPAND)
        
        sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        return sizer
    
    def _create_dynamic_config(self, parent):
        """创建动态配置区域"""
        # 创建sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 动态配置面板
        self.config_panel = wx.Panel(parent)
        self.config_sizer = wx.BoxSizer(wx.VERTICAL)
        self.config_panel.SetSizer(self.config_sizer)
        
        sizer.Add(self.config_panel, 1, wx.EXPAND)
        
        # 初始化默认配置
        self.on_type_changed(None)
        
        return sizer
    
    def _create_buttons(self, parent):
        """创建按钮区域"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 保存按钮
        self.save_button = wx.Button(parent, label="保存", id=wx.ID_OK)
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save)
        
        # 取消按钮
        self.cancel_button = wx.Button(parent, label="取消", id=wx.ID_CANCEL)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)
        
        # 添加到sizer
        sizer.Add(self.save_button, 0, wx.RIGHT, 10)
        sizer.Add(self.cancel_button, 1, wx.EXPAND)
        
        return sizer
    
    def _load_provider_config(self):
        """加载提供商配置"""
        try:
            # 设置提供商类型
            provider_type = self.provider.get('type', 'index TTS')
            if provider_type in self.provider_types:
                self.type_combo.SetValue(provider_type)
            
            # 设置自定义名称
            custom_name = self.provider.get('custom_name', '')
            self.name_text.SetValue(custom_name)
            
            # 加载动态配置
            self._load_dynamic_config()
            
        except Exception as e:
            wx.MessageBox(f"加载配置失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def _load_server_config(self):
        """加载服务器配置"""
        try:
            # 设置提供商类型
            self.type_combo.SetValue('index TTS')
            
            # 设置服务器地址
            if hasattr(self, 'server_address_text'):
                self.server_address_text.SetValue(self.server_data.get('address', ''))
            
            # 设置端口
            if hasattr(self, 'web_port_text'):
                self.web_port_text.SetValue(str(self.server_data.get('web_port', 7860)))
            
            if hasattr(self, 'synth_port_text'):
                self.synth_port_text.SetValue(str(self.server_data.get('synth_port', 9880)))
            
        except Exception as e:
            print(f"加载服务器配置失败: {e}")
    
    def on_type_changed(self, event):
        """提供商类型改变事件"""
        # 清空动态配置
        self.config_sizer.Clear(True)
        
        # 获取选择的类型
        provider_type = self.type_combo.GetValue()
        
        # 根据类型创建配置界面
        if provider_type == "index TTS":
            self._create_index_tts_config()
        else:
            self._create_generic_config()
        
        # 重新布局
        self.config_panel.Layout()
        self.config_panel.Refresh()
    
    def _create_index_tts_config(self):
        """创建index TTS配置界面"""
        # 创建静态框
        static_box = wx.StaticBox(self.config_panel, label="index TTS 配置")
        sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        
        # 创建网格布局
        grid_sizer = wx.FlexGridSizer(rows=4, cols=2, vgap=8, hgap=10)
        grid_sizer.AddGrowableCol(1, 1)
        
        # 服务器地址
        server_label = wx.StaticText(self.config_panel, label="服务器地址:")
        self.server_address_text = wx.TextCtrl(self.config_panel)
        grid_sizer.Add(server_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.server_address_text, 0, wx.EXPAND)
        
        # Web接口端口
        web_port_label = wx.StaticText(self.config_panel, label="Web接口端口:")
        self.web_port_text = wx.TextCtrl(self.config_panel, value="7860")
        grid_sizer.Add(web_port_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.web_port_text, 0, wx.EXPAND)
        
        # 合成接口端口
        synth_port_label = wx.StaticText(self.config_panel, label="合成接口端口:")
        self.synth_port_text = wx.TextCtrl(self.config_panel, value="9880")
        grid_sizer.Add(synth_port_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.synth_port_text, 0, wx.EXPAND)
        
        # 搜索按钮
        scan_button = wx.Button(self.config_panel, label="搜索局域网")
        scan_button.Bind(wx.EVT_BUTTON, self.on_scan_network)
        grid_sizer.AddStretchSpacer()
        grid_sizer.Add(scan_button, 0, wx.ALIGN_RIGHT)
        
        sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 添加到主sizer
        self.config_sizer.Add(sizer, 0, wx.EXPAND)
        
        # 创建试听文本配置
        self._create_preview_text_config()
    
    def _create_generic_config(self):
        """创建通用配置界面"""
        # 创建静态框
        static_box = wx.StaticBox(self.config_panel, label="通用配置")
        sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        
        # 创建网格布局
        grid_sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=8, hgap=10)
        grid_sizer.AddGrowableCol(1, 1)
        
        # API地址
        api_label = wx.StaticText(self.config_panel, label="API地址:")
        self.api_url_text = wx.TextCtrl(self.config_panel)
        grid_sizer.Add(api_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.api_url_text, 0, wx.EXPAND)
        
        # API密钥
        api_key_label = wx.StaticText(self.config_panel, label="API密钥:")
        self.api_key_text = wx.TextCtrl(self.config_panel)
        grid_sizer.Add(api_key_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.api_key_text, 0, wx.EXPAND)
        
        sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 添加到主sizer
        self.config_sizer.Add(sizer, 0, wx.EXPAND)
    
    def _create_preview_text_config(self):
        """创建试听文本配置"""
        # 创建静态框
        static_box = wx.StaticBox(self.config_panel, label="试听文本")
        sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        
        # 文本框
        self.preview_text = wx.TextCtrl(
            self.config_panel,
            value="这是一段默认的试听文本，用于测试语音合成效果。",
            style=wx.TE_MULTILINE | wx.TE_RICH2
        )
        self.preview_text.SetMinSize((-1, 80))
        
        sizer.Add(self.preview_text, 0, wx.EXPAND | wx.ALL, 10)
        
        # 添加到主sizer
        self.config_sizer.Add(sizer, 0, wx.EXPAND | wx.TOP, 10)
    
    def _load_dynamic_config(self):
        """加载动态配置"""
        provider_type = self.type_combo.GetValue()
        
        if provider_type == "index TTS":
            # 加载index TTS配置
            if hasattr(self, 'server_address_text'):
                self.server_address_text.SetValue(self.provider.get('server_address', ''))
            
            if hasattr(self, 'web_port_text'):
                self.web_port_text.SetValue(str(self.provider.get('web_port', 7860)))
            
            if hasattr(self, 'synth_port_text'):
                self.synth_port_text.SetValue(str(self.provider.get('synth_port', 9880)))
            
            if hasattr(self, 'preview_text'):
                self.preview_text.SetValue(self.provider.get('preview_text', ''))
    
    def on_scan_network(self, event):
        """搜索局域网事件"""
        try:
            import wx.lib.newevent
            
            # 创建自定义事件
            ScanCompleteEvent, EVT_SCAN_COMPLETE = wx.lib.newevent.NewEvent()
            
            # 禁用搜索按钮
            button = event.GetEventObject()
            button.Enable(False)
            button.SetLabel("正在搜索...")
            
            # 在后台线程中搜索
            import threading
            threading.Thread(
                target=self._scan_network_thread,
                args=(button,),
                daemon=True
            ).start()
            
        except Exception as e:
            wx.MessageBox(f"搜索失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def _scan_network_thread(self, button):
        """在后台线程中搜索局域网"""
        try:
            # 这里应该调用网络扫描器
            # 暂时模拟搜索结果
            import time
            time.sleep(2)
            
            # 模拟找到服务器
            server_data = {
                'address': '192.168.1.100',
                'web_port': 7860,
                'synth_port': 9880
            }
            
            # 在主线程中更新界面
            wx.CallAfter(self._update_server_config, server_data, button)
            
        except Exception as e:
            wx.CallAfter(wx.MessageBox, f"搜索失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            wx.CallAfter(self._restore_scan_button, button)
    
    def _update_server_config(self, server_data, button):
        """更新服务器配置"""
        try:
            # 更新配置
            if hasattr(self, 'server_address_text'):
                self.server_address_text.SetValue(server_data['address'])
            
            if hasattr(self, 'web_port_text'):
                self.web_port_text.SetValue(str(server_data['web_port']))
            
            if hasattr(self, 'synth_port_text'):
                self.synth_port_text.SetValue(str(server_data['synth_port']))
            
            wx.MessageBox("找到服务器并自动填充配置", "成功", wx.OK | wx.ICON_INFORMATION)
            
        except Exception as e:
            wx.MessageBox(f"更新配置失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
        finally:
            self._restore_scan_button(button)
    
    def _restore_scan_button(self, button):
        """恢复搜索按钮"""
        button.Enable(True)
        button.SetLabel("搜索局域网")
    
    def on_save(self, event):
        """保存配置"""
        try:
            # 验证配置
            if not self._validate_config():
                return
            
            # 生成配置数据
            self.config_data = self._generate_config_data()
            
            # 关闭对话框
            self.EndModal(wx.ID_OK)
            
        except Exception as e:
            wx.MessageBox(f"保存配置失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def on_cancel(self, event):
        """取消配置"""
        self.EndModal(wx.ID_CANCEL)
    
    def _validate_config(self):
        """验证配置"""
        # 检查提供商类型
        provider_type = self.type_combo.GetValue()
        if not provider_type:
            wx.MessageBox("请选择提供商类型", "提示", wx.OK | wx.ICON_INFORMATION)
            return False
        
        # 根据类型验证配置
        if provider_type == "index TTS":
            return self._validate_index_tts_config()
        else:
            return self._validate_generic_config()
    
    def _validate_index_tts_config(self):
        """验证index TTS配置"""
        # 检查服务器地址
        server_address = self.server_address_text.GetValue().strip()
        if not server_address:
            wx.MessageBox("请输入服务器地址", "提示", wx.OK | wx.ICON_INFORMATION)
            self.server_address_text.SetFocus()
            return False
        
        # 检查Web端口
        web_port = self.web_port_text.GetValue().strip()
        if not web_port:
            wx.MessageBox("请输入Web接口端口", "提示", wx.OK | wx.ICON_INFORMATION)
            self.web_port_text.SetFocus()
            return False
        
        try:
            web_port = int(web_port)
            if not (1 <= web_port <= 65535):
                wx.MessageBox("Web端口必须在1-65535之间", "提示", wx.OK | wx.ICON_INFORMATION)
                self.web_port_text.SetFocus()
                return False
        except ValueError:
            wx.MessageBox("Web端口必须是数字", "提示", wx.OK | wx.ICON_INFORMATION)
            self.web_port_text.SetFocus()
            return False
        
        # 检查合成端口
        synth_port = self.synth_port_text.GetValue().strip()
        if not synth_port:
            wx.MessageBox("请输入合成接口端口", "提示", wx.OK | wx.ICON_INFORMATION)
            self.synth_port_text.SetFocus()
            return False
        
        try:
            synth_port = int(synth_port)
            if not (1 <= synth_port <= 65535):
                wx.MessageBox("合成端口必须在1-65535之间", "提示", wx.OK | wx.ICON_INFORMATION)
                self.synth_port_text.SetFocus()
                return False
        except ValueError:
            wx.MessageBox("合成端口必须是数字", "提示", wx.OK | wx.ICON_INFORMATION)
            self.synth_port_text.SetFocus()
            return False
        
        return True
    
    def _validate_generic_config(self):
        """验证通用配置"""
        # 检查API地址
        api_url = self.api_url_text.GetValue().strip()
        if not api_url:
            wx.MessageBox("请输入API地址", "提示", wx.OK | wx.ICON_INFORMATION)
            self.api_url_text.SetFocus()
            return False
        
        return True
    
    def _generate_config_data(self):
        """生成配置数据"""
        # 基本信息
        config_data = {
            'id': str(uuid.uuid4()),
            'type': self.type_combo.GetValue(),
            'custom_name': self.name_text.GetValue().strip(),
            'enabled': True,
            'created_time': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'last_used': None
        }
        
        # 根据类型添加配置
        provider_type = config_data['type']
        if provider_type == "index TTS":
            config_data.update({
                'server_address': self.server_address_text.GetValue().strip(),
                'web_port': int(self.web_port_text.GetValue().strip()),
                'synth_port': int(self.synth_port_text.GetValue().strip()),
                'preview_text': self.preview_text.GetValue().strip()
            })
        else:
            config_data.update({
                'api_url': self.api_url_text.GetValue().strip(),
                'api_key': self.api_key_text.GetValue().strip()
            })
        
        return config_data
    
    def get_config_data(self):
        """获取配置数据"""
        return self.config_data