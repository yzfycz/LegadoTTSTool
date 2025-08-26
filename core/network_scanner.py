#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络扫描器模块
用于发现和验证局域网内的TTS服务器
"""

import socket
import threading
import time
import ipaddress
import wx
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from gradio_client import Client
except ImportError:
    print("Warning: gradio_client not installed, network scanning will be limited")

from utils.network_info import get_primary_network_segment, NetworkInfo
from utils.logger import get_logger

logger = get_logger()

class NetworkScanner:
    """网络扫描器"""
    
    def __init__(self):
        """初始化网络扫描器"""
        self.timeout = 1.5  # 适当增加超时时间，提高扫描稳定性
        self.max_threads = 80  # 减少线程数，减少网络竞争
        
        # index TTS 端口
        self.index_tts_ports = {
            'web': 7860,
            'synth': 9880
        }
        
        # 网络信息获取器
        self.network_info = NetworkInfo()
        
        logger.debug("网络扫描器初始化完成（稳定性优化模式）")
    
    def scan_index_tts_servers(self) -> List[Dict[str, Any]]:
        """扫描index TTS服务器 - 快速扫描"""
        try:
            logger.info("开始快速扫描index TTS服务器")
            
            # 快速扫描策略
            servers = []
            
            # 策略1：首先检查已知的服务器（从配置中）
            known_servers = self._get_known_servers()
            if known_servers:
                logger.info(f"检查 {len(known_servers)} 个已知服务器")
                servers.extend(self._verify_servers(known_servers))
            
            # 如果已知服务器不够，再进行网络扫描
            if len(servers) < 3:
                logger.info("已知服务器不足，开始网络扫描")
                
                # 获取要扫描的IP列表（优化后的快速扫描）
                ip_list = self._get_scan_ips()
                
                if not ip_list:
                    logger.warning("没有可扫描的IP地址")
                    return servers
                
                logger.log_network_operation("扫描开始", f"快速扫描 {len(ip_list)} 个IP地址")
                
                # 扫描端口
                live_hosts = self._scan_ports(ip_list)
                logger.debug(f"发现 {len(live_hosts)} 个存活主机")
                
                # 验证服务
                scanned_servers = self._verify_servers(live_hosts)
                servers.extend(scanned_servers)
            
            # 去重
            unique_servers = []
            seen_addresses = set()
            for server in servers:
                address = server['address']
                if address not in seen_addresses:
                    seen_addresses.add(address)
                    unique_servers.append(server)
            
            logger.info(f"快速扫描完成，找到 {len(unique_servers)} 个服务器")
            return unique_servers
            
        except Exception as e:
            logger.error(f"扫描服务器失败: {e}")
            return []
    
    def _get_known_servers(self) -> List[Dict[str, Any]]:
        """从配置中获取已知的服务器"""
        try:
            known_servers = []
            
            # 从当前配置中获取服务器
            try:
                from core.provider_manager import ProviderManager
                provider_manager = ProviderManager()
                providers = provider_manager.get_all_providers()
                
                for provider in providers:
                    if provider.get('enabled', True) and provider.get('server_address'):
                        server = {
                            'address': provider['server_address'],
                            'web_port': provider.get('web_port', 7860),
                            'synth_port': provider.get('synth_port', 9880)
                        }
                        known_servers.append(server)
                        logger.debug(f"添加已知服务器: {server['address']}:{server['web_port']}")
            except Exception as e:
                logger.debug(f"获取已知服务器失败: {e}")
            
            # 添加本机地址
            local_server = {
                'address': '127.0.0.1',
                'web_port': 7860,
                'synth_port': 9880
            }
            known_servers.append(local_server)
            
            return known_servers
            
        except Exception as e:
            logger.debug(f"获取已知服务器失败: {e}")
            return []
    
    def scan_network(self, segment: str) -> List[Dict[str, Any]]:
        """扫描指定网段的服务器"""
        try:
            logger.info(f"开始扫描网段: {segment}")
            
            # 生成IP列表
            ip_list = []
            for i in range(1, 256):
                ip = f"{segment}.{i}"
                ip_list.append(ip)
            
            logger.log_network_operation("扫描开始", f"扫描 {len(ip_list)} 个IP地址")
            
            # 扫描端口
            live_hosts = self._scan_ports(ip_list)
            logger.debug(f"发现 {len(live_hosts)} 个存活主机")
            
            # 验证服务
            servers = self._verify_servers(live_hosts)
            logger.info(f"扫描完成，找到 {len(servers)} 个服务器")
            
            return servers
            
        except Exception as e:
            logger.error(f"扫描网段失败: {e}")
            return []
    
    def scan_and_select_server(self) -> Optional[Dict[str, Any]]:
        """扫描并让用户选择服务器"""
        try:
            # 扫描服务器
            servers = self.scan_index_tts_servers()
            
            if not servers:
                # 没有找到服务器
                return None
            
            if len(servers) == 1:
                # 只有一个服务器，直接返回
                return servers[0]
            else:
                # 多个服务器，返回服务器列表让调用者处理UI
                return servers
                
        except Exception as e:
            print(f"扫描服务器失败: {e}")
            return None
    
    def scan_servers_only(self) -> List[Dict[str, Any]]:
        """仅扫描服务器，不涉及UI操作"""
        try:
            return self.scan_index_tts_servers()
        except Exception as e:
            print(f"扫描服务器失败: {e}")
            return []
    
    def _let_user_choose_server(self, servers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """让用户选择服务器"""
        try:
            import wx
            
            # 创建选择对话框 - 使用最简单的方式
            dialog = wx.Dialog(None, title="选择TTS服务器", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
            
            # 直接在dialog上创建控件，不使用panel
            sizer = wx.BoxSizer(wx.VERTICAL)
            
            # 添加提示文本
            prompt = wx.StaticText(dialog, label="找到多个TTS服务器，请选择一个：")
            sizer.Add(prompt, 0, wx.ALL, 10)
            
            # 添加服务器列表
            list_ctrl = wx.ListCtrl(dialog, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
            list_ctrl.InsertColumn(0, "地址", width=120)
            list_ctrl.InsertColumn(1, "Web端口", width=80)
            list_ctrl.InsertColumn(2, "合成端口", width=80)
            list_ctrl.InsertColumn(3, "状态", width=80)
            
            # 添加服务器到列表
            for i, server in enumerate(servers):
                address = server['address']
                web_port = str(server.get('web_port', 'N/A'))
                synth_port = str(server.get('synth_port', 'N/A'))
                
                # 检查服务器状态
                status = "可用" if self._check_server_status(server) else "不可用"
                
                index = list_ctrl.InsertItem(i, address)
                list_ctrl.SetItem(index, 1, web_port)
                list_ctrl.SetItem(index, 2, synth_port)
                list_ctrl.SetItem(index, 3, status)
            
            sizer.Add(list_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
            
            # 添加按钮 - 使用dialog作为父窗口
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            
            # 创建确定按钮
            ok_button = wx.Button(dialog, wx.ID_OK, "确定")
            button_sizer.Add(ok_button, 0, wx.RIGHT, 5)
            
            # 创建取消按钮
            cancel_button = wx.Button(dialog, wx.ID_CANCEL, "取消")
            button_sizer.Add(cancel_button, 0, wx.LEFT, 5)
            
            sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
            
            # 设置dialog的sizer
            dialog.SetSizer(sizer)
            
            # 设置对话框大小
            dialog.SetSize((500, 300))
            
            # 绑定键盘事件，支持回车键确定
            list_ctrl.Bind(wx.EVT_KEY_DOWN, lambda event: self._on_list_key_down(event, dialog, servers, list_ctrl))
            
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
    
    def _check_server_status(self, server: Dict[str, Any]) -> bool:
        """检查服务器状态"""
        try:
            address = server['address']
            web_port = server.get('web_port')
            synth_port = server.get('synth_port')
            
            # 优先检查Web端口
            if web_port and self._is_port_open(address, web_port):
                return True
            
            # 如果Web端口不可用，检查合成端口
            if synth_port and self._is_port_open(address, synth_port):
                return True
            
            return False
            
        except Exception as e:
            print(f"检查服务器状态失败: {e}")
            return False
    
    def _get_scan_ips(self) -> List[str]:
        """获取要扫描的IP列表 - 使用智能网段检测和快速扫描策略"""
        ip_list = []
        
        try:
            # 获取主要网段
            primary_segment = self.network_info.get_primary_network_segment()
            
            if primary_segment:
                # 扫描主要网段
                primary_ips = self._scan_segment_with_strategy(primary_segment)
                ip_list.extend(primary_ips)
                logger.info(f"主要网段扫描: {primary_segment} (共{len(primary_ips)}个IP)")
                
                # 尝试获取其他网段，增加扫描完整性
                try:
                    all_segments = self.network_info.get_network_segments()
                    other_segments = [s for s in all_segments if s != primary_segment]
                    
                    # 如果有其他网段，选择性扫描一些重要IP
                    if other_segments:
                        logger.info(f"发现其他网段: {other_segments}，将进行补充扫描")
                        
                        # 对其他网段只扫描关键IP（1-10, 200-210）
                        for segment in other_segments[:2]:  # 最多扫描2个额外网段
                            critical_ips = []
                            for i in range(1, 11):  # 1-10
                                critical_ips.append(f"{segment}.{i}")
                            for i in range(200, 211):  # 200-210
                                critical_ips.append(f"{segment}.{i}")
                            
                            ip_list.extend(critical_ips)
                            logger.info(f"补充扫描网段: {segment} (共{len(critical_ips)}个关键IP)")
                except Exception as e:
                    logger.debug(f"获取其他网段失败: {e}")
                
            else:
                # 如果获取网段失败，使用默认IP
                ip_list.extend(self._get_default_ips())
                logger.warning("无法获取网段，使用默认IP列表")
                
        except Exception as e:
            logger.error(f"获取扫描IP列表失败: {e}")
            ip_list.extend(self._get_default_ips())
        
        logger.debug(f"生成IP列表: {len(ip_list)} 个地址")
        return ip_list
    
    def _scan_segment_with_strategy(self, segment: str) -> List[str]:
        """使用智能策略扫描指定网段"""
        priority_ips = []
        
        # 优先扫描常见IP：1-20 (路由器、服务器等)
        for i in range(1, 21):
            priority_ips.append(f"{segment}.{i}")
        
        # 扫描常见设备范围：200-254 (DHCP分配范围)
        for i in range(200, 255):
            priority_ips.append(f"{segment}.{i}")
        
        # 如果优先IP不够，再补充一些中间范围
        if len(priority_ips) < 50:
            for i in range(100, 121):
                priority_ips.append(f"{segment}.{i}")
        
        return priority_ips
    
    def _get_default_ips(self) -> List[str]:
        """获取默认扫描IP列表"""
        default_ips = []
        
        # 只搜索本机回环地址作为最后的备用方案
        default_ips.append("127.0.0.1")
        
        return default_ips
    
    def _scan_ports(self, ip_list: List[str]) -> List[Dict[str, Any]]:
        """扫描端口"""
        live_hosts = []
        
        logger.debug(f"开始扫描 {len(ip_list)} 个IP的端口")
        
        # 使用线程池加速扫描
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # 提交扫描任务
            future_to_ip = {
                executor.submit(self._check_host_ports, ip): ip 
                for ip in ip_list
            }
            
            # 收集结果
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    result = future.result()
                    if result:
                        live_hosts.append(result)
                        logger.debug(f"发现存活主机: {ip}")
                except Exception as e:
                    logger.debug(f"扫描 {ip} 失败: {e}")
        
        logger.debug(f"端口扫描完成，发现 {len(live_hosts)} 个存活主机")
        return live_hosts
    
    def _check_host_ports(self, ip: str) -> Optional[Dict[str, Any]]:
        """检查主机端口"""
        result = {
            'address': ip,
            'web_port': None,
            'synth_port': None
        }
        
        # 检查Web端口
        if self._is_port_open(ip, self.index_tts_ports['web']):
            result['web_port'] = self.index_tts_ports['web']
        
        # 检查合成端口
        if self._is_port_open(ip, self.index_tts_ports['synth']):
            result['synth_port'] = self.index_tts_ports['synth']
        
        # 至少有一个端口开放
        if result['web_port'] or result['synth_port']:
            return result
        
        return None
    
    def _is_port_open(self, ip: str, port: int) -> bool:
        """检查端口是否开放"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            result = sock.connect_ex((ip, port))
            sock.close()
            
            return result == 0
            
        except Exception as e:
            return False
    
    def _verify_servers(self, live_hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证服务器"""
        verified_servers = []
        
        for host in live_hosts:
            try:
                if self._verify_index_tts_server(host):
                    verified_servers.append(host)
            except Exception as e:
                print(f"验证服务器 {host['address']} 失败: {e}")
        
        return verified_servers
    
    def _verify_index_tts_server(self, host: Dict[str, Any]) -> bool:
        """验证index TTS服务器"""
        try:
            # 优先验证Web端口
            if host.get('web_port'):
                if self._verify_gradio_api(host['address'], host['web_port']):
                    return True
            
            # 如果Web端口验证失败，尝试验证合成端口
            if host.get('synth_port'):
                if self._verify_synth_api(host['address'], host['synth_port']):
                    return True
            
            return False
            
        except Exception as e:
            print(f"验证服务器失败: {e}")
            return False
    
    def _verify_gradio_api(self, ip: str, port: int) -> bool:
        """验证Gradio API"""
        try:
            # 尝试创建Gradio客户端
            client = Client(f"http://{ip}:{port}/")
            
            # 尝试调用API
            result = client.predict(api_name="/change_choices")
            
            # 检查结果
            if isinstance(result, list) and len(result) > 0:
                print(f"验证成功: {ip}:{port} - 找到 {len(result)} 个角色")
                return True
            
            return False
            
        except Exception as e:
            print(f"Gradio API验证失败 {ip}:{port}: {e}")
            return False
    
    def _verify_synth_api(self, ip: str, port: int) -> bool:
        """验证合成API"""
        try:
            # 尝试HTTP请求
            import requests
            
            url = f"http://{ip}:{port}/"
            response = requests.get(url, timeout=self.timeout)
            
            # 检查响应状态
            if response.status_code == 200:
                print(f"合成API验证成功: {ip}:{port}")
                return True
            
            return False
            
        except Exception as e:
            print(f"合成API验证失败 {ip}:{port}: {e}")
            return False
    
    def scan_single_host(self, ip: str) -> Optional[Dict[str, Any]]:
        """扫描单个主机"""
        try:
            result = self._check_host_ports(ip)
            if result and self._verify_index_tts_server(result):
                return result
            return None
        except Exception as e:
            print(f"扫描单个主机失败: {e}")
            return None
    
    def get_network_info(self) -> Dict[str, Any]:
        """获取网络信息"""
        try:
            import psutil
            
            # 获取所有网络接口
            interfaces = psutil.net_if_addrs()
            
            network_info = {
                'interfaces': {},
                'timeout': self.timeout,
                'max_threads': self.max_threads
            }
            
            for interface_name, interface_addresses in interfaces.items():
                addresses = []
                for address in interface_addresses:
                    if address.family == socket.AF_INET:
                        addresses.append({
                            'ip': address.address,
                            'netmask': address.netmask,
                            'broadcast': address.broadcast
                        })
                
                if addresses:
                    network_info['interfaces'][interface_name] = addresses
            
            return network_info
            
        except ImportError:
            print("psutil not available, limited network info")
            return {'error': 'psutil not available'}
        except Exception as e:
            print(f"获取网络信息失败: {e}")
            return {'error': str(e)}
    
    def set_scan_config(self, timeout: int = None, max_threads: int = None):
        """设置扫描配置"""
        if timeout is not None:
            self.timeout = timeout
        
        if max_threads is not None:
            self.max_threads = max_threads
    
    def ping_host(self, ip: str) -> bool:
        """ping主机"""
        try:
            import subprocess
            
            # Windows系统使用ping命令
            result = subprocess.run(
                ['ping', '-n', '1', '-w', str(self.timeout * 1000), ip],
                capture_output=True,
                text=True,
                timeout=self.timeout + 2
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Ping失败: {e}")
            return False
    
    def get_port_info(self, port: int) -> Dict[str, Any]:
        """获取端口信息"""
        port_info = {
            7860: {
                'name': 'Gradio Web Interface',
                'description': 'index TTS Web界面端口',
                'protocol': 'HTTP'
            },
            9880: {
                'name': 'Synthesis Interface',
                'description': 'index TTS合成接口端口',
                'protocol': 'HTTP'
            }
        }
        
        return port_info.get(port, {
            'name': f'Port {port}',
            'description': 'Unknown port',
            'protocol': 'Unknown'
        })
    
    def validate_ip_address(self, ip: str) -> bool:
        """验证IP地址格式"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def validate_port_range(self, port_range: str) -> bool:
        """验证端口范围格式"""
        try:
            if '-' in port_range:
                start, end = port_range.split('-')
                start_port = int(start)
                end_port = int(end)
                
                return (1 <= start_port <= 65535 and 
                       1 <= end_port <= 65535 and 
                       start_port <= end_port)
            else:
                port = int(port_range)
                return 1 <= port <= 65535
                
        except ValueError:
            return False
    
    def estimate_scan_time(self, ip_count: int) -> float:
        """估算扫描时间"""
        # 每个IP大约需要 timeout * 2 秒（两个端口）
        time_per_ip = self.timeout * 2
        total_time = ip_count * time_per_ip
        
        # 考虑线程池并发
        concurrent_factor = min(self.max_threads, ip_count)
        estimated_time = total_time / concurrent_factor
        
        return estimated_time
    
    def _on_list_key_down(self, event, dialog, servers, list_ctrl):
        """处理服务器列表的键盘事件"""
        try:
            import wx
            
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