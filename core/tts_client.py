#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS客户端模块
用于与TTS服务进行通信，包括角色获取和语音合成
"""

import requests
import time
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlencode
import tempfile
import os

def safe_print(message: str) -> None:
    """安全打印函数，处理编码问题"""
    try:
        print(message)
    except UnicodeEncodeError:
        # 如果编码失败，移除特殊字符后重试
        cleaned_message = message.encode('ascii', errors='ignore').decode('ascii')
        print(cleaned_message)

try:
    from gradio_client import Client
    import gradio_client
except ImportError:
    safe_print("Warning: gradio_client not installed, some features may not work")

class TTSClient:
    """TTS客户端"""
    
    def __init__(self):
        """初始化TTS客户端"""
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1
    
    def _build_server_url(self, server_address: str, web_port: int = None) -> str:
        """构建服务器URL"""
        if not server_address:
            raise ValueError("服务器地址不能为空")
        
        # 如果服务器地址已经包含协议，直接使用
        if server_address.startswith(('http://', 'https://')):
            return server_address.rstrip('/')
        
        # 如果有端口号，添加端口
        if web_port:
            return f"http://{server_address}:{web_port}".rstrip('/')
        else:
            return f"http://{server_address}".rstrip('/')
    
    def get_roles(self, provider: Dict[str, Any]) -> List[str]:
        """获取角色列表"""
        try:
            provider_type = provider.get('type')
            
            if provider_type == 'index-tts':
                return self._get_index_tts_roles(provider)
            elif provider_type == 'generic':
                return self._get_generic_roles(provider)
            else:
                raise Exception(f"不支持的提供商类型: {provider_type}")
                
        except Exception as e:
            raise Exception(f"获取角色列表失败: {e}")
    
    def _get_index_tts_roles(self, provider: Dict[str, Any]) -> List[str]:
        """获取index-tts角色列表"""
        try:
            server_address = provider.get('server_address')
            web_port = provider.get('web_port', 7860)
            
            if not server_address:
                raise Exception("服务器地址不能为空")
            
            # 重定向标准输出以避免gradio_client的Unicode输出问题
            import sys
            import io
            old_stdout = sys.stdout
            # 使用StringIO捕获输出
            sys.stdout = io.StringIO()
            
            try:
                # 构建服务器URL
                server_url = self._build_server_url(server_address, web_port)
                client = Client(f"{server_url}/")
            finally:
                # 恢复标准输出
                sys.stdout = old_stdout
            
            # 调用API获取角色列表 - 不传递参数
            result = client.predict(api_name="/change_choices")
            
            # 验证结果并解析不同格式
            roles = []
            
            if isinstance(result, list):
                # 直接是列表格式
                for role in result:
                    if isinstance(role, str) and role.strip():
                        roles.append(role.strip())
            
            elif isinstance(result, dict):
                # 字典格式，包含choices键
                if 'choices' in result and isinstance(result['choices'], list):
                    choices = result['choices']
                    # choices可能是二维数组 [display_name, value]
                    for choice in choices:
                        if isinstance(choice, list) and len(choice) > 0:
                            # 取第一个元素作为显示名称
                            role_name = choice[0]
                            if isinstance(role_name, str) and role_name.strip():
                                roles.append(role_name.strip())
                        elif isinstance(choice, str) and choice.strip():
                            roles.append(choice.strip())
                else:
                    safe_print(f"字典中没有找到choices键: {result.keys()}")
                    raise Exception("API返回的字典格式不正确")
            else:
                # 不支持的格式
                safe_print(f"API返回类型: {type(result)}")
                safe_print(f"API返回内容: {result}")
                raise Exception(f"API返回格式错误: {type(result)}")
            
            safe_print(f"获取到 {len(roles)} 个角色")
            return roles
                
        except Exception as e:
            safe_print(f"获取index-tts角色失败详情: {e}")
            raise Exception(f"获取index-tts角色失败: {e}")
    
    def _get_generic_roles(self, provider: Dict[str, Any]) -> List[str]:
        """获取通用角色列表"""
        try:
            api_url = provider.get('api_url')
            api_key = provider.get('api_key')
            
            if not api_url:
                raise Exception("API地址不能为空")
            
            # 构建请求头
            headers = {}
            if api_key:
                headers['Authorization'] = f"Bearer {api_key}"
            
            # 发送请求
            response = requests.get(
                f"{api_url}/voices",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 解析角色列表
                roles = []
                if isinstance(data, dict) and 'voices' in data:
                    for voice in data['voices']:
                        if isinstance(voice, dict) and 'name' in voice:
                            roles.append(voice['name'])
                elif isinstance(data, list):
                    for voice in data:
                        if isinstance(voice, dict) and 'name' in voice:
                            roles.append(voice['name'])
                        elif isinstance(voice, str):
                            roles.append(voice)
                
                return roles
            else:
                raise Exception(f"API请求失败: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"获取通用角色失败: {e}")
    
    def preview_speech(self, provider: Dict[str, Any], role: str, text: str, speed: float = 1.0, volume: float = 1.0) -> bytes:
        """预览语音"""
        try:
            provider_type = provider.get('type')
            
            if provider_type == 'index-tts':
                return self._preview_index_tts_speech(provider, role, text, speed, volume)
            elif provider_type == 'generic':
                return self._preview_generic_speech(provider, role, text, speed, volume)
            else:
                raise Exception(f"不支持的提供商类型: {provider_type}")
                
        except Exception as e:
            raise Exception(f"语音合成失败: {e}")
    
    def _preview_index_tts_speech(self, provider: Dict[str, Any], role: str, text: str, speed: float, volume: float) -> bytes:
        """预览index-tts语音"""
        try:
            server_address = provider.get('server_address')
            synth_port = provider.get('synth_port')
            
            if not server_address:
                raise Exception("服务器地址不能为空")
            
            # 构建服务器URL
            base_url = self._build_server_url(server_address, synth_port)
            
            # 构建请求参数
            params = {
                'text': text,
                'speaker': role,
                'speed': speed,
                'volume': volume
            }
            
            # 发送请求
            response = requests.get(
                base_url,
                params=params,
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                # 检查内容类型
                content_type = response.headers.get('content-type', '').lower()
                if 'audio' in content_type:
                    return response.content
                else:
                    raise Exception(f"返回的不是音频文件: {content_type}")
            else:
                raise Exception(f"语音合成失败: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"index-tts语音合成失败: {e}")
    
    def _preview_generic_speech(self, provider: Dict[str, Any], role: str, text: str, speed: float, volume: float) -> bytes:
        """预览通用语音"""
        try:
            api_url = provider.get('api_url')
            api_key = provider.get('api_key')
            
            if not api_url:
                raise Exception("API地址不能为空")
            
            # 构建请求数据
            data = {
                'text': text,
                'voice': role,
                'speed': speed,
                'volume': volume
            }
            
            # 构建请求头
            headers = {
                'Content-Type': 'application/json'
            }
            if api_key:
                headers['Authorization'] = f"Bearer {api_key}"
            
            # 发送请求
            response = requests.post(
                f"{api_url}/synthesize",
                json=data,
                headers=headers,
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                # 检查内容类型
                content_type = response.headers.get('content-type', '').lower()
                if 'audio' in content_type:
                    return response.content
                else:
                    raise Exception(f"返回的不是音频文件: {content_type}")
            else:
                raise Exception(f"语音合成失败: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"通用语音合成失败: {e}")
    
    def test_connection(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """测试连接"""
        try:
            provider_type = provider.get('type')
            start_time = time.time()
            
            if provider_type == 'index-tts':
                result = self._test_index_tts_connection(provider)
            elif provider_type == 'generic':
                result = self._test_generic_connection(provider)
            else:
                raise Exception(f"不支持的提供商类型: {provider_type}")
            
            # 计算响应时间
            end_time = time.time()
            result['response_time'] = round((end_time - start_time) * 1000, 2)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': 0
            }
    
    def _test_index_tts_connection(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """测试index-tts连接"""
        try:
            server_address = provider.get('server_address')
            web_port = provider.get('web_port', 7860)
            synth_port = provider.get('synth_port', 9880)
            
            if not server_address:
                raise Exception("服务器地址不能为空")
            
            # 测试Web端口
            web_result = self._test_http_connection(server_address, web_port)
            
            # 测试合成端口
            synth_result = self._test_http_connection(server_address, synth_port)
            
            # 尝试获取角色列表
            roles = []
            if web_result['success']:
                try:
                    roles = self._get_index_tts_roles(provider)
                except:
                    pass
            
            return {
                'success': web_result['success'] or synth_result['success'],
                'web_port_accessible': web_result['success'],
                'synth_port_accessible': synth_result['success'],
                'roles_count': len(roles),
                'roles_sample': roles[:3] if roles else []
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_generic_connection(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """测试通用连接"""
        try:
            api_url = provider.get('api_url')
            api_key = provider.get('api_key')
            
            if not api_url:
                raise Exception("API地址不能为空")
            
            # 测试API连接
            headers = {}
            if api_key:
                headers['Authorization'] = f"Bearer {api_key}"
            
            response = requests.get(
                f"{api_url}/health",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # 尝试获取角色列表
                roles = []
                try:
                    roles = self._get_generic_roles(provider)
                except:
                    pass
                
                return {
                    'success': True,
                    'roles_count': len(roles),
                    'roles_sample': roles[:3] if roles else []
                }
            else:
                raise Exception(f"API请求失败: {response.status_code}")
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_http_connection(self, host: str, port: int = None) -> Dict[str, Any]:
        """测试HTTP连接"""
        try:
            # 构建测试URL
            if host.startswith(('http://', 'https://')):
                # 如果是完整的URL，直接使用
                test_url = f"{host}/".rstrip('/')
            elif port:
                # 如果有端口号，添加端口
                test_url = f"http://{host}:{port}/"
            else:
                # 否则使用默认的HTTP
                test_url = f"http://{host}/"
            
            response = requests.get(
                test_url,
                timeout=self.timeout
            )
            
            return {
                'success': True,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', '')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_provider_info(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """获取提供商信息"""
        try:
            provider_type = provider.get('type')
            
            if provider_type == 'index-tts':
                return self._get_index_tts_info(provider)
            elif provider_type == 'generic':
                return self._get_generic_info(provider)
            else:
                return {
                    'type': provider_type,
                    'supported': False,
                    'error': '不支持的提供商类型'
                }
                
        except Exception as e:
            return {
                'type': provider.get('type', 'unknown'),
                'supported': False,
                'error': str(e)
            }
    
    def _get_index_tts_info(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """获取index-tts信息"""
        try:
            server_address = provider.get('server_address')
            web_port = provider.get('web_port', 7860)
            
            if not server_address:
                return {
                    'type': 'index-tts',
                    'supported': True,
                    'configured': False,
                    'error': '服务器地址未配置'
                }
            
            # 尝试获取版本信息
            try:
                server_url = self._build_server_url(server_address, web_port)
                client = Client(f"{server_url}/")
                # 这里可以添加获取版本信息的API调用
                version = "unknown"
            except:
                version = "unknown"
            
            return {
                'type': 'index_tts',
                'supported': True,
                'configured': True,
                'version': version,
                'server_address': server_address,
                'web_port': web_port,
                'synth_port': provider.get('synth_port', 9880)
            }
            
        except Exception as e:
            return {
                'type': 'index_tts',
                'supported': True,
                'configured': False,
                'error': str(e)
            }
    
    def _get_generic_info(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """获取通用提供商信息"""
        try:
            api_url = provider.get('api_url')
            
            if not api_url:
                return {
                    'type': 'generic',
                    'supported': True,
                    'configured': False,
                    'error': 'API地址未配置'
                }
            
            return {
                'type': 'generic',
                'supported': True,
                'configured': True,
                'api_url': api_url
            }
            
        except Exception as e:
            return {
                'type': 'generic',
                'supported': True,
                'configured': False,
                'error': str(e)
            }
    
    def set_timeout(self, timeout: int):
        """设置超时时间"""
        self.timeout = timeout
    
    def set_max_retries(self, max_retries: int):
        """设置最大重试次数"""
        self.max_retries = max_retries
    
    def set_retry_delay(self, retry_delay: int):
        """设置重试延迟"""
        self.retry_delay = retry_delay