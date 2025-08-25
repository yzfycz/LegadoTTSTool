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
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from gradio_client import Client
except ImportError:
    print("Warning: gradio_client not installed, network scanning will be limited")

class NetworkScanner:
    """网络扫描器"""
    
    def __init__(self):
        """初始化网络扫描器"""
        self.timeout = 3
        self.max_threads = 50
        
        # index TTS 端口
        self.index_tts_ports = {
            'web': 7860,
            'synth': 9880
        }
    
    def scan_index_tts_servers(self) -> List[Dict[str, Any]]:
        """扫描index TTS服务器"""
        try:
            print("开始扫描index TTS服务器...")
            
            # 获取要扫描的IP列表
            ip_list = self._get_scan_ips()
            
            # 扫描端口
            live_hosts = self._scan_ports(ip_list)
            
            # 验证服务
            servers = self._verify_servers(live_hosts)
            
            print(f"扫描完成，找到 {len(servers)} 个服务器")
            return servers
            
        except Exception as e:
            print(f"扫描服务器失败: {e}")
            return []
    
    def _get_scan_ips(self) -> List[str]:
        """获取要扫描的IP列表 - 只搜索本机网段"""
        ip_list = []
        
        try:
            # 获取本机IP地址
            local_ip = self._get_local_ip()
            if local_ip:
                # 提取网段
                ip_parts = local_ip.split('.')
                if len(ip_parts) == 4:
                    # 生成网段内的所有IP (1-254)
                    network_segment = '.'.join(ip_parts[:-1])
                    for i in range(1, 255):
                        ip = f"{network_segment}.{i}"
                        ip_list.append(ip)
                    print(f"检测到本机IP: {local_ip}, 搜索网段: {network_segment}.1-254")
                else:
                    # 如果IP格式不正确，搜索默认网段
                    ip_list.extend(self._get_default_ips())
            else:
                # 如果无法获取本机IP，搜索默认网段
                ip_list.extend(self._get_default_ips())
                
        except Exception as e:
            print(f"获取扫描IP列表失败: {e}")
            ip_list.extend(self._get_default_ips())
        
        return ip_list
    
    def _get_local_ip(self) -> Optional[str]:
        """获取本机IP地址"""
        try:
            # 创建一个UDP套接字连接到公共DNS服务器
            # 这样可以获取本机用于外网通信的IP地址
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            return local_ip
        except Exception:
            # 如果失败，尝试获取主机名
            try:
                local_ip = socket.gethostbyname(socket.gethostname())
                return local_ip
            except Exception:
                return None
    
    def _get_default_ips(self) -> List[str]:
        """获取默认扫描IP列表"""
        default_ips = []
        
        # 添加一些常见的私有IP地址
        common_ips = [
            "192.168.1.1",
            "192.168.0.1",
            "10.0.0.1",
            "127.0.0.1"
        ]
        
        for ip in common_ips:
            ip_parts = ip.split('.')
            if len(ip_parts) == 4:
                network_segment = '.'.join(ip_parts[:-1])
                for i in range(1, 11):  # 只搜索前10个IP
                    test_ip = f"{network_segment}.{i}"
                    default_ips.append(test_ip)
        
        return default_ips
    
    def _scan_ports(self, ip_list: List[str]) -> List[Dict[str, Any]]:
        """扫描端口"""
        live_hosts = []
        
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
                except Exception as e:
                    print(f"扫描 {ip} 失败: {e}")
        
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
                'scan_ranges': self.scan_ranges,
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
    
    def set_scan_config(self, timeout: int = None, max_threads: int = None, scan_ranges: List[str] = None):
        """设置扫描配置"""
        if timeout is not None:
            self.timeout = timeout
        
        if max_threads is not None:
            self.max_threads = max_threads
        
        if scan_ranges is not None:
            self.scan_ranges = scan_ranges
    
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