#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络信息获取模块
使用系统命令获取真实的网络适配器信息
"""

import subprocess
import re
import platform
from typing import List, Dict, Tuple, Optional
from utils.logger import get_logger

logger = get_logger()

# 全局实例
_network_info = None

def get_network_adapters():
    """获取所有网络适配器信息"""
    global _network_info
    if _network_info is None:
        _network_info = NetworkInfo()
    return _network_info.get_network_adapters()

def get_network_segments():
    """获取所有网络网段"""
    global _network_info
    if _network_info is None:
        _network_info = NetworkInfo()
    return _network_info.get_network_segments()

def get_primary_network_segment():
    """获取主要网络网段"""
    global _network_info
    if _network_info is None:
        _network_info = NetworkInfo()
    return _network_info.get_primary_network_segment()

class NetworkInfo:
    """网络信息获取器"""
    
    def __init__(self):
        """初始化网络信息获取器"""
        self.os_type = platform.system().lower()
        logger.debug(f"操作系统类型: {self.os_type}")
    
    def get_network_adapters(self) -> List[Dict[str, str]]:
        """获取所有网络适配器信息"""
        try:
            logger.debug("开始获取网络适配器信息")
            
            if self.os_type == "windows":
                adapters = self._get_windows_adapters()
            elif self.os_type == "linux":
                adapters = self._get_linux_adapters()
            elif self.os_type == "darwin":
                adapters = self._get_macos_adapters()
            else:
                logger.warning(f"不支持的操作系统: {self.os_type}")
                adapters = []
            
            logger.log_function_call("get_network_adapters", {"count": len(adapters)})
            return adapters
            
        except Exception as e:
            logger.error(f"获取网络适配器信息失败: {e}")
            return []
    
    def _get_windows_adapters(self) -> List[Dict[str, str]]:
        """获取Windows网络适配器信息"""
        adapters = []
        
        try:
            # 执行ipconfig /all命令
            result = subprocess.run(
                ["ipconfig", "/all"],
                capture_output=True,
                text=True,
                encoding="gbk",  # Windows使用GBK编码
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"ipconfig命令执行失败: {result.stderr}")
                return adapters
            
            output = result.stdout
            logger.debug(f"ipconfig输出长度: {len(output)} 字符")
            
            # 解析输出
            current_adapter = {}
            lines = output.split('\n')
            
            for line in lines:
                original_line = line
                line = line.strip()
                
                # 检测适配器名称 - 更准确的识别
                if (line and not line.startswith(' ') and ':' in line and 
                    ('适配器' in line or 'adapter' in line.lower() or 
                     '以太网' in line or 'WiFi' in line or 'WLAN' in line or
                     'Tunnel' in line or 'Bluetooth' in line)):
                    
                    # 保存前一个适配器（如果有）
                    if current_adapter and current_adapter.get('name'):
                        adapters.append(current_adapter)
                    
                    # 开始新的适配器
                    adapter_name = line.split(':')[0].strip()
                    current_adapter = {
                        'name': adapter_name,
                        'type': self._detect_adapter_type(adapter_name),
                        'status': '未知',
                        'ipv4': [],
                        'description': ''
                    }
                    
                    logger.debug(f"发现适配器: {adapter_name}")
                
                # 如果当前有适配器，解析其属性
                elif current_adapter:
                    # 解析适配器状态
                    if '媒体状态' in line or 'Media state' in line:
                        if '已连接' in line or 'connected' in line.lower():
                            current_adapter['status'] = '已连接'
                        else:
                            current_adapter['status'] = '未连接'
                    
                    # 解析描述信息
                    elif '描述' in line and ':' in line:
                        description = line.split(':', 1)[1].strip()
                        current_adapter['description'] = description
                    
                    # 解析IPv4地址
                    elif 'IPv4 地址' in line or 'IPv4 Address' in line:
                        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                        if ip_match:
                            ip = ip_match.group(1)
                            # 过滤掉私有地址和特殊地址，保留有效的局域网IP
                            if not (ip.startswith('127.') or ip.startswith('169.254.') or ip == '0.0.0.0'):
                                current_adapter['ipv4'].append(ip)
                                logger.debug(f"  IPv4地址: {ip}")
                    
                    # 如果有IPv4地址但没有明确状态，假设是已连接的
                    elif current_adapter['ipv4'] and current_adapter['status'] == '未知':
                        current_adapter['status'] = '已连接'
            
            # 保存最后一个适配器
            if current_adapter:
                adapters.append(current_adapter)
            
            # 过滤出有效的适配器 - 放宽条件
            valid_adapters = []
            for adapter in adapters:
                # 只要有IP地址就认为是有效的适配器
                if adapter['ipv4']:
                    # 如果没有明确的状态，假设是已连接的
                    if adapter['status'] == '未知':
                        adapter['status'] = '已连接'
                    valid_adapters.append(adapter)
                    logger.debug(f"有效适配器: {adapter['name']} ({adapter['type']}) - {adapter['status']} - {adapter['ipv4']}")
            
            logger.info(f"找到 {len(valid_adapters)} 个有效网络适配器")
            return valid_adapters
            
        except Exception as e:
            logger.error(f"获取Windows网络适配器失败: {e}")
            return []
    
    def _get_linux_adapters(self) -> List[Dict[str, str]]:
        """获取Linux网络适配器信息"""
        adapters = []
        
        try:
            # 执行ifconfig命令
            result = subprocess.run(
                ["ifconfig"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"ifconfig命令执行失败: {result.stderr}")
                return adapters
            
            output = result.stdout
            logger.debug("解析Linux网络适配器信息")
            
            # 解析输出（简化版本）
            current_adapter = {}
            lines = output.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # 检测适配器名称
                if line and not line.startswith(' ') and ':' in line:
                    # 保存前一个适配器（如果有）
                    if current_adapter:
                        adapters.append(current_adapter)
                    
                    # 开始新的适配器
                    adapter_name = line.split(':')[0].strip()
                    current_adapter = {
                        'name': adapter_name,
                        'type': self._detect_adapter_type(adapter_name),
                        'status': '已连接',
                        'ipv4': []
                    }
                    
                    logger.debug(f"发现适配器: {adapter_name}")
                
                # 解析IPv4地址
                elif 'inet ' in line and 'netmask' in line:
                    ip_match = re.search(r'inet\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                    if ip_match:
                        ip = ip_match.group(1)
                        # 只保留192.168.x.x网段的IP
                        if ip.startswith('192.168.'):
                            current_adapter['ipv4'].append(ip)
                            logger.debug(f"  IPv4地址: {ip}")
            
            # 保存最后一个适配器
            if current_adapter:
                adapters.append(current_adapter)
            
            # 过滤出有效的适配器
            valid_adapters = []
            for adapter in adapters:
                if (adapter['type'] in ['以太网', 'WiFi'] and adapter['ipv4']):
                    valid_adapters.append(adapter)
                    logger.debug(f"有效适配器: {adapter['name']} - {adapter['ipv4']}")
            
            logger.info(f"找到 {len(valid_adapters)} 个有效网络适配器")
            return valid_adapters
            
        except Exception as e:
            logger.error(f"获取Linux网络适配器失败: {e}")
            return []
    
    def _get_macos_adapters(self) -> List[Dict[str, str]]:
        """获取macOS网络适配器信息"""
        # macOS与Linux类似，使用ifconfig
        return self._get_linux_adapters()
    
    def _detect_adapter_type(self, adapter_name: str) -> str:
        """检测适配器类型"""
        adapter_name_lower = adapter_name.lower()
        
        # WiFi适配器关键词
        wifi_keywords = ['wi-fi', 'wireless', 'wlan', 'wifi', '802.11', 'airport']
        
        # 以太网适配器关键词
        ethernet_keywords = ['ethernet', 'local area connection', 'lan', '以太网', '本地连接']
        
        # 检查WiFi
        for keyword in wifi_keywords:
            if keyword in adapter_name_lower:
                logger.debug(f"  识别为WiFi适配器: {adapter_name}")
                return 'WiFi'
        
        # 检查以太网
        for keyword in ethernet_keywords:
            if keyword in adapter_name_lower:
                logger.debug(f"  识别为以太网适配器: {adapter_name}")
                return '以太网'
        
        # 默认返回其他
        logger.debug(f"  识别为其他适配器: {adapter_name}")
        return '其他'
    
    def get_network_segments(self) -> List[str]:
        """获取所有网络网段"""
        try:
            logger.debug("开始获取网络网段")
            
            adapters = self.get_network_adapters()
            segments = set()
            
            for adapter in adapters:
                for ip in adapter['ipv4']:
                    # 提取网段 (如 192.168.1.100 -> 192.168.1)
                    segment = '.'.join(ip.split('.')[:3])
                    segments.add(segment)
                    logger.debug(f"  提取网段: {segment} (来自 {ip})")
            
            segments_list = list(segments)
            logger.info(f"获取到网段: {segments_list}")
            
            return segments_list
            
        except Exception as e:
            logger.error(f"获取网络网段失败: {e}")
            return []
    
    def get_primary_network_segment(self) -> Optional[str]:
        """获取主要网络网段"""
        try:
            segments = self.get_network_segments()
            
            if not segments:
                logger.warning("未找到任何网络网段")
                return None
            
            if len(segments) == 1:
                # 只有一个网段，直接返回
                primary_segment = segments[0]
                logger.info(f"使用唯一网段: {primary_segment}")
                return primary_segment
            else:
                # 多个网段，优先选择以太网
                adapters = self.get_network_adapters()
                
                # 优先选择以太网
                for adapter in adapters:
                    if adapter['type'] == '以太网' and adapter['ipv4']:
                        segment = '.'.join(adapter['ipv4'][0].split('.')[:3])
                        logger.info(f"选择以太网网段: {segment}")
                        return segment
                
                # 其次选择WiFi
                for adapter in adapters:
                    if adapter['type'] == 'WiFi' and adapter['ipv4']:
                        segment = '.'.join(adapter['ipv4'][0].split('.')[:3])
                        logger.info(f"选择WiFi网段: {segment}")
                        return segment
                
                # 最后选择第一个网段
                primary_segment = segments[0]
                logger.info(f"使用第一个网段: {primary_segment}")
                return primary_segment
                
        except Exception as e:
            logger.error(f"获取主要网络网段失败: {e}")
            return None