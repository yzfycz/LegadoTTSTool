#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络信息获取模块
使用系统命令获取真实的网络适配器信息
支持基于IP网段的智能过滤
"""

import subprocess
import re
import platform
import ipaddress
from typing import List, Dict, Tuple, Optional, Any
from utils.logger import get_logger

logger = get_logger()

# 网段分类优先级（从高到低）
SEGMENT_CATEGORIES = {
    'HIGH_PRIORITY': {
        'name': '高优先级网段',
        'description': '真实局域网和内网穿透网段',
        'segments': [
            '192.168.0.0/16',     # 家庭/办公室局域网
            '10.0.0.0/8',         # 企业局域网
            '172.16.0.0/12',      # 企业局域网 (172.16.0.0 - 172.31.255.255)
        ],
        'scan_mode': 'FULL'      # 完整扫描
    },
    
    'MEDIUM_PRIORITY': {
        'name': '中优先级网段', 
        'description': '可能的内网穿透网段',
        'segments': [
            '100.64.0.0/10',      # CGNAT空间 (100.64.0.0 - 100.127.255.255)
            '169.254.0.0/16',     # APIPA自动私有IP (169.254.0.0 - 169.254.255.255)
        ],
        'scan_mode': 'FAST'      # 快速扫描
    },
    
    'LOW_PRIORITY': {
        'name': '低优先级网段',
        'description': '虚拟网卡和特殊网段',
        'segments': [
            '172.17.0.0/16',      # Docker默认网段
            '172.18.0.0/16',      # Docker网段
            '172.19.0.0/16',      # Docker网段
            '172.20.0.0/16',      # Docker网段
            '172.21.0.0/16',      # Docker网段
            '172.22.0.0/16',      # Docker网段
            '172.23.0.0/16',      # Docker网段
            '172.24.0.0/16',      # Docker网段
            '172.25.0.0/16',      # Docker网段
            '172.26.0.0/16',      # Docker网段
            '172.27.0.0/16',      # Docker网段
            '172.28.0.0/16',      # Docker网段
            '172.29.0.0/16',      # Docker网段
            '172.30.0.0/16',      # Docker网段
            '172.31.0.0/16',      # Docker网段 (已被HIGH_PRIORITY包含，这里保持完整性)
        ],
        'scan_mode': 'SKIP'       # 跳过扫描
    },
    
    'SPECIAL_PRIORITY': {
        'name': '特殊网段',
        'description': '需要特殊处理的网段',
        'segments': [
            '127.0.0.0/8',        # 回环地址
            '224.0.0.0/4',        # 组播地址
            '255.255.255.255/32', # 广播地址
            '0.0.0.0/8',          # 默认路由
        ],
        'scan_mode': 'IGNORE'     # 完全忽略
    }
}

# 内网穿透工具网段模式
TUNNELING_PATTERNS = {
    'ngrok': [
        r'^192\.168\.(99|100)\.\d+$',     # ngrok常用网段
        r'^10\.0\.(99|100)\.\d+$',        # ngrok备用网段
    ],
    'frp': [
        r'^192\.168\.(200|201)\.\d+$',    # frp常用网段
        r'^172\.16\.(200|201)\.\d+$',     # frp备用网段
    ],
    'custom_tunnel': [
        r'^192\.168\.(1\d\d|2\d\d)\.\d+$', # 自定义内网穿透网段
        r'^10\.(1\d\d|2\d\d)\.\d+\.\d+$',   # 自定义内网穿透网段
    ]
}

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

class SegmentClassifier:
    """网段智能分类器"""
    
    def __init__(self):
        self.categories = SEGMENT_CATEGORIES
        self.tunneling_patterns = TUNNELING_PATTERNS
    
    def classify_segment(self, segment: str) -> Dict[str, Any]:
        """分类网段并返回扫描策略"""
        # 1. 检查是否为特殊网段
        if self._is_special_segment(segment):
            return {
                'category': 'SPECIAL_PRIORITY',
                'priority': 0,
                'scan_mode': 'IGNORE',
                'reason': '特殊网段'
            }
        
        # 2. 检查是否为高优先级网段
        if self._is_high_priority_segment(segment):
            return {
                'category': 'HIGH_PRIORITY', 
                'priority': 3,
                'scan_mode': 'FULL',
                'reason': '真实局域网网段'
            }
        
        # 3. 检查是否为内网穿透网段
        if self._is_tunneling_segment(segment):
            return {
                'category': 'HIGH_PRIORITY',
                'priority': 2,
                'scan_mode': 'FULL', 
                'reason': '内网穿透网段'
            }
        
        # 4. 检查是否为中优先级网段
        if self._is_medium_priority_segment(segment):
            return {
                'category': 'MEDIUM_PRIORITY',
                'priority': 1,
                'scan_mode': 'FAST',
                'reason': '可能的内网穿透网段'
            }
        
        # 5. 默认为低优先级网段
        return {
            'category': 'LOW_PRIORITY',
            'priority': 0,
            'scan_mode': 'SKIP',
            'reason': '虚拟网卡网段'
        }
    
    def _is_high_priority_segment(self, segment: str) -> bool:
        """检查是否为高优先级网段"""
        high_segments = self.categories['HIGH_PRIORITY']['segments']
        return self._segment_in_ranges(segment, high_segments)
    
    def _is_tunneling_segment(self, segment: str) -> bool:
        """检查是否为内网穿透网段"""
        import re
        
        for tool_name, patterns in self.tunneling_patterns.items():
            for pattern in patterns:
                # 将网段转换为正则表达式
                segment_pattern = pattern.replace(r'\d+$', r'\d+')
                if re.match(segment_pattern, f"{segment}.1"):
                    logger.debug(f"  识别为内网穿透网段: {segment} ({tool_name})")
                    return True
        return False
    
    def _is_medium_priority_segment(self, segment: str) -> bool:
        """检查是否为中优先级网段"""
        medium_segments = self.categories['MEDIUM_PRIORITY']['segments']
        return self._segment_in_ranges(segment, medium_segments)
    
    def _is_special_segment(self, segment: str) -> bool:
        """检查是否为特殊网段"""
        special_segments = self.categories['SPECIAL_PRIORITY']['segments']
        return self._segment_in_ranges(segment, special_segments)
    
    def _segment_in_ranges(self, segment: str, ranges: List[str]) -> bool:
        """检查网段是否在指定范围内"""
        try:
            # 将网段转换为网络对象
            segment_network = ipaddress.IPv4Network(f"{segment}.0/24", strict=False)
            
            for range_str in ranges:
                range_network = ipaddress.IPv4Network(range_str, strict=False)
                if segment_network.subnet_of(range_network):
                    return True
            return False
        except Exception as e:
            logger.debug(f"  网段检查失败: {segment} - {e}")
            return False


class SegmentScanEngine:
    """网段扫描策略引擎"""
    
    def __init__(self):
        self.classifier = SegmentClassifier()
    
    def get_scan_strategy(self, segments: List[str]) -> Dict[str, Any]:
        """获取扫描策略"""
        strategy = {
            'segments_to_scan': [],
            'segments_to_skip': [],
            'scan_order': [],
            'performance_estimate': {
                'total_ips': 0,
                'scan_time': 0.0,
                'time_saved': 0
            }
        }
        
        # 分类所有网段
        classified_segments = []
        for segment in segments:
            classification = self.classifier.classify_segment(segment)
            classified_segments.append({
                'segment': segment,
                'classification': classification
            })
            
            logger.debug(f"网段分类: {segment} -> {classification['category']} "
                        f"({classification['reason']})")
        
        # 按优先级排序
        classified_segments.sort(
            key=lambda x: x['classification']['priority'], 
            reverse=True
        )
        
        # 生成扫描策略
        for item in classified_segments:
            segment = item['segment']
            classification = item['classification']
            scan_mode = classification['scan_mode']
            
            if scan_mode == 'FULL':
                # 完整扫描：1-255
                strategy['segments_to_scan'].append({
                    'segment': segment,
                    'scan_range': (1, 255),
                    'mode': 'FULL',
                    'reason': classification['reason']
                })
                strategy['scan_order'].append(segment)
                strategy['performance_estimate']['total_ips'] += 254
                
            elif scan_mode == 'FAST':
                # 快速扫描：只扫描关键IP (1-10, 200-210)
                strategy['segments_to_scan'].append({
                    'segment': segment,
                    'scan_range': [(1, 10), (200, 210)],
                    'mode': 'FAST',
                    'reason': classification['reason']
                })
                strategy['scan_order'].append(segment)
                strategy['performance_estimate']['total_ips'] += 21  # 10 + 11
                
            elif scan_mode == 'SKIP':
                # 跳过扫描
                strategy['segments_to_skip'].append({
                    'segment': segment,
                    'reason': classification['reason']
                })
                strategy['performance_estimate']['time_saved'] += 254  # 估算节省的时间
        
        # 计算扫描时间 (每个IP约0.1秒)
        strategy['performance_estimate']['scan_time'] = (
            strategy['performance_estimate']['total_ips'] * 0.1
        )
        
        return strategy


class NetworkInfo:
    """网络信息获取器"""
    
    def __init__(self):
        """初始化网络信息获取器"""
        self.os_type = platform.system().lower()
        self.segment_classifier = SegmentClassifier()
        self.scan_engine = SegmentScanEngine()
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
    
    def get_filtered_network_segments(self) -> Dict[str, Any]:
        """获取过滤后的网络网段和扫描策略"""
        try:
            logger.debug("开始获取智能过滤的网络网段")
            
            # 获取所有网段
            all_segments = self.get_network_segments()
            
            if not all_segments:
                logger.warning("未找到任何网络网段")
                return {
                    'segments_to_scan': [],
                    'segments_to_skip': [],
                    'scan_order': [],
                    'performance_estimate': {
                        'total_ips': 0,
                        'scan_time': 0.0,
                        'time_saved': 0
                    }
                }
            
            # 获取扫描策略
            strategy = self.scan_engine.get_scan_strategy(all_segments)
            
            # 记录扫描策略
            logger.info(f"智能网段过滤完成:")
            logger.info(f"  扫描网段: {[s['segment'] for s in strategy['segments_to_scan']]}")
            logger.info(f"  跳过网段: {[s['segment'] for s in strategy['segments_to_skip']]}")
            logger.info(f"  预估扫描时间: {strategy['performance_estimate']['scan_time']:.1f}秒")
            logger.info(f"  节省时间: {strategy['performance_estimate']['time_saved'] * 0.1:.1f}秒")
            
            return strategy
            
        except Exception as e:
            logger.error(f"获取智能过滤网络网段失败: {e}")
            return {
                'segments_to_scan': [],
                'segments_to_skip': [],
                'scan_order': [],
                'performance_estimate': {
                    'total_ips': 0,
                    'scan_time': 0.0,
                    'time_saved': 0
                }
            }
    
    def get_primary_network_segment(self) -> Optional[str]:
        """获取主要网络网段"""
        try:
            # 使用智能过滤获取网段
            filtered_data = self.get_filtered_network_segments()
            segments_to_scan = filtered_data['segments_to_scan']
            
            if not segments_to_scan:
                logger.warning("未找到可扫描的网络网段")
                return None
            
            # 优先选择高优先级网段
            high_priority_segments = [
                s for s in segments_to_scan 
                if s['mode'] == 'FULL' and '真实局域网网段' in s['reason']
            ]
            
            if high_priority_segments:
                primary_segment = high_priority_segments[0]['segment']
                logger.info(f"选择高优先级网段: {primary_segment}")
                return primary_segment
            
            # 其次选择内网穿透网段
            tunneling_segments = [
                s for s in segments_to_scan 
                if s['mode'] == 'FULL' and '内网穿透网段' in s['reason']
            ]
            
            if tunneling_segments:
                primary_segment = tunneling_segments[0]['segment']
                logger.info(f"选择内网穿透网段: {primary_segment}")
                return primary_segment
            
            # 最后选择第一个可扫描网段
            primary_segment = segments_to_scan[0]['segment']
            logger.info(f"使用第一个可扫描网段: {primary_segment}")
            return primary_segment
                
        except Exception as e:
            logger.error(f"获取主要网络网段失败: {e}")
            return None