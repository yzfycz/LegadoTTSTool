#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提供商管理器模块
用于管理TTS提供商的增删改查操作
"""

import json
import uuid
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

class ProviderManager:
    """提供商管理器"""
    
    def __init__(self):
        """初始化提供商管理器"""
        self.config_file = Path("config/providers.json")
        self.providers = []
        
        # 确保配置目录存在
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.providers = config.get('providers', [])
            else:
                # 创建默认配置
                self._create_default_config()
                
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.providers = []
    
    def _create_default_config(self):
        """创建默认配置"""
        self.providers = []
        self._save_config()
    
    def _save_config(self):
        """保存配置文件"""
        try:
            config = {
                'providers': self.providers,
                'version': '1.0.0',
                'last_updated': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            raise Exception(f"保存配置文件失败: {e}")
    
    def get_all_providers(self) -> List[Dict[str, Any]]:
        """获取所有提供商"""
        return self.providers.copy()
    
    def get_provider_by_id(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取提供商"""
        for provider in self.providers:
            if provider.get('id') == provider_id:
                return provider
        return None
    
    def get_provider_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取提供商"""
        for provider in self.providers:
            # 检查自定义名称或类型名称
            custom_name = provider.get('custom_name', '')
            provider_type = provider.get('type', '')
            
            # 检查完整名称格式 "custom_name - type"
            full_name = f"{custom_name} - {provider_type}"
            
            if custom_name == name or provider_type == name or full_name == name:
                return provider
        return None
    
    def add_provider(self, provider_data: Dict[str, Any]) -> str:
        """添加提供商"""
        try:
            # 验证必要字段
            if 'type' not in provider_data:
                raise Exception("提供商类型不能为空")
            
            # 生成ID（如果不存在）
            if 'id' not in provider_data:
                provider_data['id'] = str(uuid.uuid4())
            
            # 设置创建时间
            if 'created_time' not in provider_data:
                provider_data['created_time'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # 设置默认值
            provider_data.setdefault('enabled', True)
            provider_data.setdefault('last_used', None)
            
            # 添加到列表
            self.providers.append(provider_data)
            
            # 保存配置
            self._save_config()
            
            return provider_data['id']
            
        except Exception as e:
            raise Exception(f"添加提供商失败: {e}")
    
    def update_provider(self, provider_id: str, provider_data: Dict[str, Any]) -> bool:
        """更新提供商"""
        try:
            # 查找提供商
            for i, provider in enumerate(self.providers):
                if provider.get('id') == provider_id:
                    # 保留原始ID和创建时间
                    provider_data['id'] = provider_id
                    provider_data['created_time'] = provider.get('created_time')
                    
                    # 更新提供商数据
                    self.providers[i] = provider_data
                    
                    # 保存配置
                    self._save_config()
                    
                    return True
            
            return False
            
        except Exception as e:
            raise Exception(f"更新提供商失败: {e}")
    
    def delete_provider(self, provider_id: str) -> bool:
        """删除提供商"""
        try:
            # 查找并删除提供商
            for i, provider in enumerate(self.providers):
                if provider.get('id') == provider_id:
                    del self.providers[i]
                    
                    # 保存配置
                    self._save_config()
                    
                    return True
            
            return False
            
        except Exception as e:
            raise Exception(f"删除提供商失败: {e}")
    
    def enable_provider(self, provider_id: str) -> bool:
        """启用提供商"""
        return self._set_provider_status(provider_id, True)
    
    def disable_provider(self, provider_id: str) -> bool:
        """禁用提供商"""
        return self._set_provider_status(provider_id, False)
    
    def _set_provider_status(self, provider_id: str, enabled: bool) -> bool:
        """设置提供商状态"""
        try:
            for provider in self.providers:
                if provider.get('id') == provider_id:
                    provider['enabled'] = enabled
                    
                    # 保存配置
                    self._save_config()
                    
                    return True
            
            return False
            
        except Exception as e:
            raise Exception(f"设置提供商状态失败: {e}")
    
    def get_enabled_providers(self) -> List[Dict[str, Any]]:
        """获取启用的提供商"""
        return [p for p in self.providers if p.get('enabled', True)]
    
    def update_last_used(self, provider_id: str):
        """更新最后使用时间"""
        try:
            for provider in self.providers:
                if provider.get('id') == provider_id:
                    provider['last_used'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    
                    # 保存配置
                    self._save_config()
                    
                    break
                    
        except Exception as e:
            print(f"更新最后使用时间失败: {e}")
    
    def validate_provider_config(self, provider_data: Dict[str, Any]) -> List[str]:
        """验证提供商配置"""
        errors = []
        
        # 验证必要字段
        required_fields = ['type']
        for field in required_fields:
            if field not in provider_data or not provider_data[field]:
                errors.append(f"{field} 字段不能为空")
        
        # 根据类型验证配置
        provider_type = provider_data.get('type')
        if provider_type == 'index_tts':
            errors.extend(self._validate_index_tts_config(provider_data))
        elif provider_type == 'generic':
            errors.extend(self._validate_generic_config(provider_data))
        
        return errors
    
    def _validate_index_tts_config(self, provider_data: Dict[str, Any]) -> List[str]:
        """验证index TTS配置"""
        errors = []
        
        # 验证服务器地址
        if 'server_address' not in provider_data or not provider_data['server_address']:
            errors.append("服务器地址不能为空")
        
        # 验证端口
        port_fields = ['web_port', 'synth_port']
        for field in port_fields:
            if field not in provider_data or not provider_data[field]:
                errors.append(f"{field} 不能为空")
            elif not isinstance(provider_data[field], int) or not (1 <= provider_data[field] <= 65535):
                errors.append(f"{field} 必须是1-65535之间的整数")
        
        return errors
    
    def _validate_generic_config(self, provider_data: Dict[str, Any]) -> List[str]:
        """验证通用配置"""
        errors = []
        
        # 验证API地址
        if 'api_url' not in provider_data or not provider_data['api_url']:
            errors.append("API地址不能为空")
        
        return errors
    
    def get_provider_statistics(self) -> Dict[str, Any]:
        """获取提供商统计信息"""
        total_providers = len(self.providers)
        enabled_providers = len(self.get_enabled_providers())
        
        # 按类型统计
        type_counts = {}
        for provider in self.providers:
            provider_type = provider.get('type', 'unknown')
            type_counts[provider_type] = type_counts.get(provider_type, 0) + 1
        
        return {
            'total_providers': total_providers,
            'enabled_providers': enabled_providers,
            'disabled_providers': total_providers - enabled_providers,
            'type_distribution': type_counts
        }
    
    def backup_config(self, backup_path: str) -> bool:
        """备份配置文件"""
        try:
            import shutil
            shutil.copy2(self.config_file, backup_path)
            return True
        except Exception as e:
            print(f"备份配置文件失败: {e}")
            return False
    
    def restore_config(self, backup_path: str) -> bool:
        """恢复配置文件"""
        try:
            import shutil
            shutil.copy2(backup_path, self.config_file)
            
            # 重新加载配置
            self._load_config()
            
            return True
        except Exception as e:
            print(f"恢复配置文件失败: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """导出配置文件"""
        try:
            config = {
                'providers': self.providers,
                'version': '1.0.0',
                'exported_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"导出配置文件失败: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """导入配置文件"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # 验证配置格式
                if 'providers' not in config:
                    raise Exception("配置文件格式不正确")
                
                # 合并配置
                existing_ids = {p.get('id') for p in self.providers}
                
                for provider in config['providers']:
                    # 生成新的ID避免冲突
                    if provider.get('id') in existing_ids:
                        provider['id'] = str(uuid.uuid4())
                    
                    # 重置时间戳
                    provider['created_time'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    provider['last_used'] = None
                    
                    self.providers.append(provider)
                
                # 保存配置
                self._save_config()
                
                return True
                
        except Exception as e:
            print(f"导入配置文件失败: {e}")
            return False