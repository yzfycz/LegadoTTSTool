#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案配置对话框模块
用于创建和编辑TTS方案配置
"""

import wx
import wx.lib.scrolledpanel
import uuid
import time
from typing import List, Dict, Any, Optional

from core.network_scanner import NetworkScanner

class ConfigDialog(wx.Dialog):
    """方案配置对话框"""
    
    def __init__(self, parent, title="配置方案", provider=None, server_data=None):
        """初始化配置对话框"""
        super().__init__(
            parent, 
            title=title, 
            size=(500, 400),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        # 方案数据
        self.provider = provider
        self.server_data = server_data
        
        # 配置数据
        self.config_data = {}
        
        # 支持的方案类型
        self.provider_types = ["index-tts"]
        
        # 初始化界面
        self._init_ui()
        
        # 如果有方案数据，加载配置
        if provider:
            self._load_provider_config()
        elif server_data:
            self._load_server_config()
        else:
            # 设置默认值
            self.type_combo.SetValue("index-tts")
            self.on_type_changed(None)
        
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
        
        # 方案类型
        type_label = wx.StaticText(parent, label="方案类型:")
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
            provider_type = self.provider.get('type', 'index-tts')
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
            self.type_combo.SetValue('index-tts')
            
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
        
        # 如果没有选择的类型，使用默认类型
        if not provider_type:
            provider_type = "index-tts"
            self.type_combo.SetValue(provider_type)
        
        # 根据类型创建配置界面
        if provider_type == "index-tts":
            self._create_index_tts_config()
        else:
            self._create_generic_config()
        
        # 重新布局
        self.config_panel.Layout()
        self.config_panel.Refresh()
        
        # 如果是编辑模式，重新加载配置
        if self.provider:
            self._load_dynamic_config()
    
    def _create_index_tts_config(self):
        """创建index-tts配置界面"""
        # 创建静态框
        static_box = wx.StaticBox(self.config_panel, label="index-tts 配置")
        sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        
        # 创建网格布局
        grid_sizer = wx.FlexGridSizer(rows=5, cols=2, vgap=8, hgap=10)
        grid_sizer.AddGrowableCol(1, 1)
        
        # 服务器地址
        server_label = wx.StaticText(self.config_panel, label="服务器地址:")
        self.server_address_text = wx.TextCtrl(self.config_panel)
        grid_sizer.Add(server_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.server_address_text, 0, wx.EXPAND)
        
        # Web接口端口（非必填）
        web_port_label = wx.StaticText(self.config_panel, label="Web接口端口:")
        self.web_port_text = wx.TextCtrl(self.config_panel, value="7860")
        grid_sizer.Add(web_port_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.web_port_text, 0, wx.EXPAND)
        
        # 合成接口端口（非必填）
        synth_port_label = wx.StaticText(self.config_panel, label="合成接口端口:")
        self.synth_port_text = wx.TextCtrl(self.config_panel, value="9880")
        grid_sizer.Add(synth_port_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.synth_port_text, 0, wx.EXPAND)
        
        # 连接超时时间
        timeout_label = wx.StaticText(self.config_panel, label="连接超时时间(秒):")
        self.timeout_text = wx.TextCtrl(self.config_panel, value="30")
        timeout_help = wx.StaticText(self.config_panel, label="0表示无超时")
        grid_sizer.Add(timeout_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        timeout_sizer = wx.BoxSizer(wx.HORIZONTAL)
        timeout_sizer.Add(self.timeout_text, 1, wx.EXPAND)
        timeout_sizer.Add(timeout_help, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer.Add(timeout_sizer, 0, wx.EXPAND)
        
        # 搜索按钮
        scan_button = wx.Button(self.config_panel, label="搜索局域网")
        scan_button.Bind(wx.EVT_BUTTON, self.on_scan_network)
        grid_sizer.AddStretchSpacer()
        grid_sizer.Add(scan_button, 0, wx.ALIGN_RIGHT)
        
        sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 添加到主sizer
        self.config_sizer.Add(sizer, 0, wx.EXPAND)
    
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
    
        
    def _load_dynamic_config(self):
        """加载动态配置"""
        provider_type = self.type_combo.GetValue()
        
        if provider_type == "index-tts":
            # 加载index-tts配置
            if hasattr(self, 'server_address_text'):
                self.server_address_text.SetValue(self.provider.get('server_address', ''))
            
            if hasattr(self, 'web_port_text'):
                web_port = self.provider.get('web_port', 7860)
                self.web_port_text.SetValue(str(web_port) if web_port else '')
            
            if hasattr(self, 'synth_port_text'):
                synth_port = self.provider.get('synth_port', 9880)
                self.synth_port_text.SetValue(str(synth_port) if synth_port else '')
            
            if hasattr(self, 'timeout_text'):
                timeout = self.provider.get('timeout', 30)
                self.timeout_text.SetValue(str(timeout) if timeout else '30')
    
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
            # 使用真正的网络扫描器
            scanner = NetworkScanner()
            
            # 仅扫描服务器，不涉及UI操作
            scan_result = scanner.scan_and_select_server()
            
            # 在主线程中处理结果和UI操作
            wx.CallAfter(self._handle_scan_result, scan_result, button)
            
        except Exception as e:
            wx.CallAfter(wx.MessageBox, f"搜索失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def _handle_scan_result(self, scan_result, button):
        """在主线程中处理扫描结果"""
        try:
            if scan_result is None:
                # 没有找到服务器
                wx.MessageBox("未在局域网找到index-tts服务器", "提示", wx.OK | wx.ICON_INFORMATION)
                
                # 使用默认地址
                from utils.network_info import get_primary_network_segment
                primary_segment = get_primary_network_segment()
                
                if primary_segment:
                    server_data = {
                        'address': f"{primary_segment}.100",
                        'web_port': 7860,
                        'synth_port': 9880
                    }
                else:
                    server_data = {
                        'address': '127.0.0.1',
                        'web_port': 7860,
                        'synth_port': 9880
                    }
                    
            elif isinstance(scan_result, dict):
                # 只有一个服务器，直接使用
                server_data = {
                    'address': scan_result['address'],
                    'web_port': scan_result.get('web_port', 7860),
                    'synth_port': scan_result.get('synth_port', 9880)
                }
                
            elif isinstance(scan_result, list):
                # 多个服务器，让用户选择
                selected_server = self._let_user_choose_server(scan_result)
                if selected_server:
                    server_data = {
                        'address': selected_server['address'],
                        'web_port': selected_server.get('web_port', 7860),
                        'synth_port': selected_server.get('synth_port', 9880)
                    }
                else:
                    # 用户取消了选择，使用默认地址
                    from utils.network_info import get_primary_network_segment
                    primary_segment = get_primary_network_segment()
                    
                    if primary_segment:
                        server_data = {
                            'address': f"{primary_segment}.100",
                            'web_port': 7860,
                            'synth_port': 9880
                        }
                    else:
                        server_data = {
                            'address': '127.0.0.1',
                            'web_port': 7860,
                            'synth_port': 9880
                        }
            
            # 更新界面配置
            self._update_server_config(server_data, button)
            
        except Exception as e:
            wx.MessageBox(f"处理搜索结果失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def _let_user_choose_server(self, servers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """让用户选择服务器（在主线程中调用）"""
        try:
            # 创建选择对话框 - 使用最简单的方式
            dialog = wx.Dialog(self, title="选择TTS服务器", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
            
            # 直接在dialog上创建控件，不使用panel
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # 添加提示文本
            prompt = wx.StaticText(dialog, label="找到多个TTS服务器，请选择一个：")
            main_sizer.Add(prompt, 0, wx.ALL, 10)
            
            # 添加服务器列表
            list_ctrl = wx.ListCtrl(dialog, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
            list_ctrl.InsertColumn(0, "地址", width=120)
            list_ctrl.InsertColumn(1, "Web端口", width=80)
            list_ctrl.InsertColumn(2, "合成端口", width=80)
            list_ctrl.InsertColumn(3, "状态", width=80)
            
            # 添加服务器到列表
            scanner = NetworkScanner()
            for i, server in enumerate(servers):
                address = server['address']
                web_port = str(server.get('web_port', 'N/A'))
                synth_port = str(server.get('synth_port', 'N/A'))
                
                # 检查服务器状态
                status = "可用" if scanner._check_server_status(server) else "不可用"
                
                index = list_ctrl.InsertItem(i, address)
                list_ctrl.SetItem(index, 1, web_port)
                list_ctrl.SetItem(index, 2, synth_port)
                list_ctrl.SetItem(index, 3, status)
            
            main_sizer.Add(list_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
            
            # 绑定键盘事件，支持回车键确定
            list_ctrl.Bind(wx.EVT_KEY_DOWN, lambda event: self._on_list_key_down(event, dialog, servers, list_ctrl))
            
            # 添加按钮 - 使用dialog作为父窗口
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            
            # 创建确定按钮
            ok_button = wx.Button(dialog, wx.ID_OK, "确定")
            button_sizer.Add(ok_button, 0, wx.RIGHT, 5)
            
            # 创建取消按钮
            cancel_button = wx.Button(dialog, wx.ID_CANCEL, "取消")
            button_sizer.Add(cancel_button, 0, wx.LEFT, 5)
            
            main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
            
            # 设置dialog的sizer
            dialog.SetSizer(main_sizer)
            dialog.SetSize((500, 300))
            
            # 自动将焦点设置到第一行（如果有的话）
            if list_ctrl.GetItemCount() > 0:
                list_ctrl.SetItemState(0, wx.LIST_STATE_FOCUSED | wx.LIST_STATE_SELECTED, wx.LIST_STATE_FOCUSED | wx.LIST_STATE_SELECTED)
            
            # 显示对话框
            if dialog.ShowModal() == wx.ID_OK:
                selected_index = list_ctrl.GetFirstSelected()
                if selected_index != -1:
                    chosen_server = servers[selected_index]
                    dialog.Destroy()
                    return chosen_server
                else:
                    wx.MessageBox("请先选择一个服务器", "提示", wx.OK | wx.ICON_INFORMATION)
            
            dialog.Destroy()
            return None
            
        except Exception as e:
            print(f"显示服务器选择对话框失败: {e}")
            return None
    
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
        # 检查方案类型
        provider_type = self.type_combo.GetValue()
        if not provider_type:
            wx.MessageBox("请选择方案类型", "提示", wx.OK | wx.ICON_INFORMATION)
            return False
        
        # 根据类型验证配置
        if provider_type == "index-tts":
            return self._validate_index_tts_config()
        else:
            return self._validate_generic_config()
    
    def _validate_index_tts_config(self):
        """验证index-tts配置"""
        # 检查服务器地址
        server_address = self.server_address_text.GetValue().strip()
        if not server_address:
            wx.MessageBox("请输入服务器地址", "提示", wx.OK | wx.ICON_INFORMATION)
            self.server_address_text.SetFocus()
            return False
        
        # 检查Web端口（如果填写了）
        web_port = self.web_port_text.GetValue().strip()
        if web_port:
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
        
        # 检查合成端口（如果填写了）
        synth_port = self.synth_port_text.GetValue().strip()
        if synth_port:
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
        
        # 检查超时时间
        timeout_str = self.timeout_text.GetValue().strip()
        if timeout_str:
            try:
                timeout = int(timeout_str)
                if timeout < 0:
                    wx.MessageBox("超时时间不能为负数", "提示", wx.OK | wx.ICON_INFORMATION)
                    self.timeout_text.SetFocus()
                    return False
            except ValueError:
                wx.MessageBox("超时时间必须是整数", "提示", wx.OK | wx.ICON_INFORMATION)
                self.timeout_text.SetFocus()
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
        if provider_type == "index-tts":
            # 处理端口（非必填）
            web_port = self.web_port_text.GetValue().strip()
            synth_port = self.synth_port_text.GetValue().strip()
            
            # 处理超时时间
            timeout_str = self.timeout_text.GetValue().strip()
            timeout = int(timeout_str) if timeout_str else 30
            
            config_data.update({
                'server_address': self.server_address_text.GetValue().strip(),
                'web_port': int(web_port) if web_port else None,
                'synth_port': int(synth_port) if synth_port else None,
                'timeout': timeout
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
    
    def _on_list_key_down(self, event, dialog, servers, list_ctrl):
        """处理服务器列表的键盘事件"""
        try:
            # 获取按键代码
            key_code = event.GetKeyCode()
            
            # 如果按下回车键
            if key_code == wx.WXK_RETURN:
                # 获取光标所在的行
                focused_item = list_ctrl.GetFocusedItem()
                
                if focused_item != -1:
                    # 光标在某一行上，直接返回该行的服务器
                    chosen_server = servers[focused_item]
                    dialog.EndModal(wx.ID_OK)
                    return
            
            # 如果按下ESC键
            elif key_code == wx.WXK_ESCAPE:
                # 直接关闭对话框
                dialog.EndModal(wx.ID_CANCEL)
                return
            
            # 处理上下键移动光标
            elif key_code == wx.WXK_UP:
                # 向上移动光标并自动获得焦点
                focused_item = list_ctrl.GetFocusedItem()
                if focused_item > 0:
                    # 清除原来的焦点和选中状态
                    list_ctrl.SetItemState(focused_item, 0, wx.LIST_STATE_FOCUSED | wx.LIST_STATE_SELECTED)
                    # 设置新的焦点和选中状态
                    list_ctrl.SetItemState(focused_item - 1, wx.LIST_STATE_FOCUSED | wx.LIST_STATE_SELECTED, wx.LIST_STATE_FOCUSED | wx.LIST_STATE_SELECTED)
                    list_ctrl.EnsureVisible(focused_item - 1)
                return
            
            elif key_code == wx.WXK_DOWN:
                # 向下移动光标并自动获得焦点
                focused_item = list_ctrl.GetFocusedItem()
                if focused_item < list_ctrl.GetItemCount() - 1:
                    # 清除原来的焦点和选中状态
                    list_ctrl.SetItemState(focused_item, 0, wx.LIST_STATE_FOCUSED | wx.LIST_STATE_SELECTED)
                    # 设置新的焦点和选中状态
                    list_ctrl.SetItemState(focused_item + 1, wx.LIST_STATE_FOCUSED | wx.LIST_STATE_SELECTED, wx.LIST_STATE_FOCUSED | wx.LIST_STATE_SELECTED)
                    list_ctrl.EnsureVisible(focused_item + 1)
                return
            
            # 其他按键交给默认处理
            event.Skip()
            
        except Exception as e:
            print(f"处理键盘事件失败: {e}")
            event.Skip()