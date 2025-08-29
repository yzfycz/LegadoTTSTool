#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON导出器模块
用于将角色数据导出为Legado阅读软件兼容的JSON格式
"""

import json
import time
from typing import List, Dict, Any, Set

class JSONExporter:
    """JSON导出器"""
    
    def __init__(self):
        """初始化JSON导出器"""
        self.used_ids = set()
    
    def generate_json(self, roles: List[str], provider: Dict[str, Any], speed: float = 1.0, volume: float = 1.0) -> List[Dict[str, Any]]:
        """生成JSON数据"""
        try:
            # 重置已使用ID集合
            self.used_ids = set()
            
            # 获取提供商信息
            provider_type = provider.get('type')
            custom_name = provider.get('custom_name', '')
            provider_name = provider.get('type', '')
            
            # 构建显示名称
            if custom_name:
                display_name = f"{custom_name} - {provider_name}"
            else:
                display_name = provider_name
            
            # 生成角色数据
            json_data = []
            
            for role in roles:
                try:
                    role_data = self._create_role_data(role, display_name, provider, speed, volume)
                    if role_data:
                        json_data.append(role_data)
                except Exception as e:
                    print(f"生成角色数据失败 {role}: {e}")
            
            return json_data
            
        except Exception as e:
            raise Exception(f"生成JSON数据失败: {e}")
    
    def _create_role_data(self, role: str, display_name: str, provider: Dict[str, Any], speed: float, volume: float) -> Dict[str, Any]:
        """创建角色数据"""
        try:
            # 生成唯一ID
            role_id = self._generate_unique_id()
            
            # 构建名称
            name = f"{role}_{display_name}"
            
            # 构建URL
            url = self._build_url(role, provider, speed, volume)
            
            # 创建角色数据
            role_data = {
                "concurrentRate": "0",
                "contentType": "audio/wav",
                "enabledCookieJar": False,
                "id": role_id,
                "lastUpdateTime": int(time.time() * 1000),
                "name": name,
                "url": url
            }
            
            return role_data
            
        except Exception as e:
            raise Exception(f"创建角色数据失败: {e}")
    
    def _generate_unique_id(self) -> int:
        """生成唯一的正数时间戳ID"""
        try:
            # 生成时间戳ID
            timestamp = int(time.time() * 1000)
            
            # 确保ID唯一性
            while timestamp in self.used_ids:
                timestamp += 1
            
            # 添加到已使用ID集合
            self.used_ids.add(timestamp)
            
            return timestamp
            
        except Exception as e:
            raise Exception(f"生成唯一ID失败: {e}")
    
    def _build_url(self, role: str, provider: Dict[str, Any], speed: float, volume: float) -> str:
        """构建URL"""
        try:
            provider_type = provider.get('type')
            
            if provider_type == 'index-tts':
                return self._build_index_tts_url(role, provider, speed, volume)
            elif provider_type == 'generic':
                return self._build_generic_url(role, provider, speed, volume)
            else:
                raise Exception(f"不支持的提供商类型: {provider_type}")
                
        except Exception as e:
            raise Exception(f"构建URL失败: {e}")
    
    def _build_index_tts_url(self, role: str, provider: Dict[str, Any], speed: float, volume: float) -> str:
        """构建index-tts URL"""
        try:
            server_address = provider.get('server_address')
            synth_port = provider.get('synth_port')
            
            if not server_address:
                raise Exception("服务器地址不能为空")
            
            # 构建基础URL
            if server_address.startswith(('http://', 'https://')):
                # 如果是完整的URL，直接使用
                base_url = server_address.rstrip('/')
            elif synth_port:
                # 如果有端口号，添加端口
                base_url = f"http://{server_address}:{synth_port}".rstrip('/')
            else:
                # 否则使用默认的HTTP
                base_url = f"http://{server_address}".rstrip('/')
            
            # 构建完整URL - 不进行URL编码，保持原文输出
            url = f"{base_url}?text={{{{speakText}}}}&speaker={role}&speed={speed}&volume={volume}"
            
            return url
            
        except Exception as e:
            raise Exception(f"构建index-tts URL失败: {e}")
    
    def _build_generic_url(self, role: str, provider: Dict[str, Any], speed: float, volume: float) -> str:
        """构建通用URL"""
        try:
            api_url = provider.get('api_url')
            
            if not api_url:
                raise Exception("API地址不能为空")
            
            # 构建基础URL
            base_url = api_url.rstrip('/')
            
            # 构建参数
            params = {
                'text': '{{speakText}}',
                'voice': role,
                'speed': speed,
                'volume': volume
            }
            
            # 构建完整URL - 不进行URL编码，保持原文输出
            url = f"{base_url}/synthesize?text={{{{speakText}}}}&voice={role}&speed={speed}&volume={volume}"
            
            return url
            
        except Exception as e:
            raise Exception(f"构建通用URL失败: {e}")
    
    def export_to_file(self, json_data: List[Dict[str, Any]], file_path: str):
        """导出到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            raise Exception(f"导出到文件失败: {e}")
    
    def export_to_string(self, json_data: List[Dict[str, Any]]) -> str:
        """导出到字符串"""
        try:
            return json.dumps(json_data, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"导出到字符串失败: {e}")
    
    def validate_json_data(self, json_data: List[Dict[str, Any]]) -> List[str]:
        """验证JSON数据"""
        errors = []
        
        if not isinstance(json_data, list):
            errors.append("JSON数据必须是数组")
            return errors
        
        required_fields = ['concurrentRate', 'contentType', 'enabledCookieJar', 'id', 'lastUpdateTime', 'name', 'url']
        
        for i, item in enumerate(json_data):
            if not isinstance(item, dict):
                errors.append(f"第{i+1}项必须是对象")
                continue
            
            # 检查必要字段
            for field in required_fields:
                if field not in item:
                    errors.append(f"第{i+1}项缺少必要字段: {field}")
            
            # 验证ID
            if 'id' in item:
                if not isinstance(item['id'], int) or item['id'] <= 0:
                    errors.append(f"第{i+1}项ID必须是正整数")
            
            # 验证URL
            if 'url' in item:
                if not isinstance(item['url'], str) or not item['url'].strip():
                    errors.append(f"第{i+1}项URL不能为空")
                elif not item['url'].startswith('http'):
                    errors.append(f"第{i+1}项URL必须以http开头")
            
            # 验证时间戳
            if 'lastUpdateTime' in item:
                if not isinstance(item['lastUpdateTime'], int) or item['lastUpdateTime'] <= 0:
                    errors.append(f"第{i+1}项时间戳必须是正整数")
        
        return errors
    
    def get_export_statistics(self, json_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取导出统计信息"""
        try:
            stats = {
                'total_roles': len(json_data),
                'id_range': {'min': None, 'max': None},
                'content_types': {},
                'url_protocols': {},
                'file_size_estimate': 0
            }
            
            if not json_data:
                return stats
            
            # 分析数据
            ids = []
            for item in json_data:
                # 收集ID
                if 'id' in item:
                    ids.append(item['id'])
                
                # 统计内容类型
                content_type = item.get('contentType', 'unknown')
                stats['content_types'][content_type] = stats['content_types'].get(content_type, 0) + 1
                
                # 统计URL协议
                url = item.get('url', '')
                if url.startswith('http://'):
                    stats['url_protocols']['http'] = stats['url_protocols'].get('http', 0) + 1
                elif url.startswith('https://'):
                    stats['url_protocols']['https'] = stats['url_protocols'].get('https', 0) + 1
            
            # 计算ID范围
            if ids:
                stats['id_range']['min'] = min(ids)
                stats['id_range']['max'] = max(ids)
            
            # 估算文件大小
            json_string = self.export_to_string(json_data)
            stats['file_size_estimate'] = len(json_string.encode('utf-8'))
            
            return stats
            
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return stats
    
    def create_backup(self, json_data: List[Dict[str, Any]], backup_dir: str = "backups") -> str:
        """创建备份文件"""
        try:
            import os
            from pathlib import Path
            
            # 确保备份目录存在
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 生成备份文件名
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            backup_file = backup_path / f"tts_roles_backup_{timestamp}.json"
            
            # 导出备份
            self.export_to_file(json_data, str(backup_file))
            
            return str(backup_file)
            
        except Exception as e:
            raise Exception(f"创建备份失败: {e}")
    
    def merge_json_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """合并多个JSON文件"""
        try:
            merged_data = []
            existing_ids = set()
            
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        for item in data:
                            # 检查ID冲突
                            if 'id' in item:
                                if item['id'] in existing_ids:
                                    # 生成新的ID
                                    item['id'] = self._generate_unique_id()
                                existing_ids.add(item['id'])
                            
                            merged_data.append(item)
                    
                except Exception as e:
                    print(f"读取文件失败 {file_path}: {e}")
            
            return merged_data
            
        except Exception as e:
            raise Exception(f"合并JSON文件失败: {e}")
    
    def filter_roles(self, json_data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """过滤角色"""
        try:
            filtered_data = []
            
            for item in json_data:
                include = True
                
                # 按名称过滤
                if 'name' in filters:
                    filter_name = filters['name'].lower()
                    if filter_name and filter_name not in item.get('name', '').lower():
                        include = False
                
                # 按URL过滤
                if 'url' in filters:
                    filter_url = filters['url'].lower()
                    if filter_url and filter_url not in item.get('url', '').lower():
                        include = False
                
                # 按内容类型过滤
                if 'contentType' in filters:
                    filter_type = filters['contentType']
                    if filter_type and item.get('contentType') != filter_type:
                        include = False
                
                if include:
                    filtered_data.append(item)
            
            return filtered_data
            
        except Exception as e:
            raise Exception(f"过滤角色失败: {e}")
    
    def sort_roles(self, json_data: List[Dict[str, Any]], sort_by: str = 'name', reverse: bool = False) -> List[Dict[str, Any]]:
        """排序角色"""
        try:
            def sort_key(item):
                value = item.get(sort_by, '')
                if isinstance(value, str):
                    return value.lower()
                return value
            
            return sorted(json_data, key=sort_key, reverse=reverse)
            
        except Exception as e:
            raise Exception(f"排序角色失败: {e}")
    
    def deduplicate_roles(self, json_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重角色"""
        try:
            seen_names = set()
            unique_data = []
            
            for item in json_data:
                name = item.get('name', '')
                if name not in seen_names:
                    seen_names.add(name)
                    unique_data.append(item)
            
            return unique_data
            
        except Exception as e:
            raise Exception(f"去重角色失败: {e}")